"""
A module for batching images and their associated data into bigger images - Atlas.

This is one of the most important modules in the game, as it allows us not only to group images nicely,
but also increase app's performance by performing less texture switches.

In hardware accelerated graphics, a single draw call can only take a limited amount of textures
(we'll exclude bindless for now, as it's a WAY advanced feature for me). For this reason, it would
be too slow to draw thousands of different objects with different textures at the same, as it would lead
to ... 1000 draw calls. There are numerous solutions to this, be it from batching similar geometry
together (for example, submitting multiple objects with the same texture as a single draw call), or...
we could create a single, large, unified texture with all these small textures inside... Hmmm, convenient...

For this exact reason this module implements a CPU Atlas batcher. It allows us to batch small textures
together into bigger textures. This is the lower-brick for higher-level abstractions like fonts and
texture atlases (which are exactly the same, but utilize GPU textures instead).

## Sprite
A sprite is simply a surface (image) with a rectangle region. Our atlas stores these sprites and uses
their surfaces for rerendering the surface, or adding new sprites (by checking against their rectangles).

One key design detail is that by default, while all sprites are stored under unique keys in the atlas -
a single key stores multiple sprites at a time. This is done to allow easily integrating animations, as
they don't require unique keys per every frame. For this case, internally, a single key always contains
sprite tuples (even though they always only contain a single sprite)

## Algorithm
The algorithm is dead simple:
- If the atlas is empty, the first sprite goes directly to (0, 0);
- If the atlas already contains sprites, then it's going to iterate over each, and get its corners.
A single sprite contains 7 possible corners, so the algorithm is usually N7 in its complexity (but, it's
still faster than the naive approach). If we still can't fit a sprite however - we will try to resize
the image by 2 times in a single axis (for example, going from 512x512 to 1024x512), and repeating the process.
Because we don't want our atlases to go infinite - the atlas API allows defining if the atlas is growable
and its maximum possible size (defined on 2 axis. For example, maximum size of 1024 means 1024x1024 is the limit)
"""

import pygame as pg
from itertools import chain
from typing import Any, Optional, Union

class SpriteRect:
    "An individual sprite image. It contains both the image surface and its rectangle"
    def __init__(self, surf: pg.Surface):
        self.surf = surf
        self.rect = self.surf.get_rect().copy()

    def width(self) -> int:
        return self.rect.width
    
    def height(self) -> int:
        return self.rect.height

    def corners(self, target_w: int, target_h: int) -> tuple[tuple, ...]:
        "Get spots of this texture that can be used to fit an another sprite"
        x, y, w, h = self.rect
        return (
            (x+w+1, y), # top-right
            (x, y+h+1), # bottom-left
            (x+w+1, y+h+1), # bottom-right

            (x+w+1, y-target_h-1), # up-right
            (x-target_w-1, y), # top-left

            (x+w+1, 0), # zero-right
            (0, y+h+1), # bottom-zero
        )

    def move(self, x: int, y: int):
        "Move this sprite to a new position"
        self.rect.topleft = (x, y)

    def collides(self, others: list["SpriteRect"]) -> bool:
        "Check if this sprite collides with all other sprite rectangles"
        return self.rect.collideobjects(others, key=lambda srect: srect.rect) is not None
    
    def get_rect(self) -> pg.Rect:
        return self.rect.copy()
    
    def get_size(self) -> tuple[int, int]:
        return (self.rect.width, self.rect.height)
    
    def draw(self, screen: pg.Surface):
        "Render this sprite onto a surface"
        screen.blit(self.surf, self.rect)

def scale_dimensions(size: tuple[int, int]) -> tuple[int, int]:
    "Scale the provided dimensions in a power-of-2 way"

    width, height = size
    if width <= height:
        width *= 2
    else:
        height *= 2

    return width, height

class SurfaceAtlas:
    "A CPU surface atlas for merging small images into bigger ones"
    def __init__(self, surface_size: tuple[int, int], resizable: bool, surface_limit: int):
        self.sprite_map: dict[Any, tuple[SpriteRect]] = {}
        "The map that stores sprite tuples and keys"

        self.resizable = resizable

        self.surface_width: int = surface_size[0]
        self.surface_height: int = surface_size[1]

        self.surface_limit = surface_limit
        self.taken_corners = set()
        """
        This set stores already taken corners. This is a simple optimization that allows us to ignore
        corners that were already processed.
        """

        self.new_added_sprites: list[Any] = []
        """
        This list defines all newly added sprites. The atlas doesn't need it neccessarily, but for example
        higher level abstractions like texture atlases would like to know which regions have changed.
        """

    def _can_scale(self, size: tuple[int, int]) -> bool:
        "For the provided size and our known resizability capability and surface limit, can this atlas scale further?"
        return (
            self.resizable and 
            (size[0] < self.surface_limit or size[1] < self.surface_limit)
        )

    def can_resize(self) -> bool:
        "This atlas can resize unless it's of size of `surface_limit` or isn't resizable "
        return self._can_scale(self.surface_width, self.surface_height)
    
    def _insert_sprites(self, key: Any, entries: tuple[tuple[SpriteRect, tuple[int, int]]]):
        """
        Insert the provided sprites into the sprite map, update the newly added sprites and if
        corner positions aren't `None` - will also insert the corner positions in the taken corners set.
        """

        self.sprite_map[key] = tuple(sprite_rect for sprite_rect, _ in entries)

        for sprite_rect, corner_pos in entries:
            self.new_added_sprites.append(sprite_rect)

            if corner_pos is not None:
                self.taken_corners.add(corner_pos)

    def get_size(self) -> tuple[int, int]:
        "Get the size of the atlas surface"
        return self.surface_width, self.surface_height

    def _fit_sprites(self, key: Any, new_sprites: tuple[SpriteRect]) -> bool:
        """
        The algorithm here is extremely simple: for every rectangle we already have in the map - we will iterate over
        its corners and check if our new rectangle collides with any other rectangles. It isn't the best algorithm
        for fitting of course, but it's extremely simple and efficient.

        Additional speedup is made by storing all already used corners in a set, thus we will avoid checking
        collisions for those entirely.
        """

        #Of course, we will not fit sprites that already are present
        assert not self.contains_sprites(key), f"Sprites under key {key} are already present"

        # Get all our existing sprites into this tuple. We're using the chain iterator to unpack
        # them into a single, flat tuple
        existing_rects: tuple[SpriteRect] = tuple(chain.from_iterable(self.sprite_map.values()))

        # The sprites that we have been able to fit
        fit_sprites: list[tuple[SpriteRect, Union[tuple[int, int], None]]] = []

        # Essentially the same thing, but for their rectangles. This is neccessary for later
        # collision checks
        added_rects: list[SpriteRect] = []

        surf_size = self.get_size()

        # Now we're going to perform the algorithm for every single new sprite
        for new_sprite in new_sprites:

            # This variable acts as a state machine. If it's `None` - continue the algorithm. If not - stop.
            fit_sprite: tuple[SpriteRect, None] = None

            if len(self.sprite_map) < 1:
                # If the map is empty, simply insert it at coordinates 0, 0

                # But... there is a possibility of the first sprite being too large, 
                # so we're going to make a simple loop, making sure that it actually fits
                sprite_w, sprite_h = new_sprite.width(), new_sprite.height()
                while not fit_sprite:
                    if sprite_w <= surf_size[0] and sprite_h <= surf_size[1]:
                        # If our sprite fits - we can stop the algorithm here

                        fit_sprite = (new_sprite, None)       
                    else:
                        # In any other case, we would need to resize

                        if self._can_scale(surf_size):
                            surf_size = scale_dimensions(surf_size)
                        else:
                            # But at some point we wouldn't be able to, so we'll just quit
                            break                    
            else:
                # In case a sprite already exists in an atlas - we will need to do the manual approach 
                # of checking against all sprites

                while not fit_sprite:

                    # We're going to iterate every single sprite rect (including just newly added ones)
                    rects_to_check = tuple(chain(existing_rects, added_rects))
                    for existing_rect in rects_to_check:

                        # Get the corners of this rect
                        corners = existing_rect.corners(new_sprite.width(), new_sprite.height())

                        # Now, for every corner, we're going to perform checks to make sure that they
                        # can be used
                        for (x, y) in corners:                        
                            if (x, y) in self.taken_corners:
                                # The corner is already taken
                                continue
                            elif x > surf_size[0]-new_sprite.width() or y > surf_size[1]-new_sprite.height():
                                # Our sprite doesn't fit under said corner
                                continue
                            elif x < 0 or y < 0:
                                # Our sprite is outside the atlas under said corner
                                continue
                            
                            # If the corner is valid - we're going to move our sprite and test collisions
                            new_sprite.move(x, y)
                            if not new_sprite.collides(rects_to_check):
                                # If it doesn't - great, we now have fit our sprite!
                                fit_sprite = (new_sprite, (x, y))
                                break
                        
                        if fit_sprite:
                            # An early break in case we did find the sprite
                            # Python doesn't have branch labels, so...
                            break
                    
                    if not fit_sprite:
                        # Again, if we weren't able to fit - we will have to resize
                        if self._can_scale(surf_size):
                            surf_size = scale_dimensions(surf_size)
                        else:
                            break
            
            # Finally, regardless how we have fit our sprite - we can now add it to the fit sprites
            if fit_sprite:
                fit_sprites.append(fit_sprite) # Add it to the general sprite list, for final registration
                added_rects.append(new_sprite) # Add its rectangle, so we can check collisions against it
            else:
                # We're going to quit early, as there's no reason to check other sprites if one has failed
                return False
        
        # We have reached the end of our algorithm! We can register our sprites!

        # If during the process our atlas size has changed - we need to resize it
        if surf_size != self.get_size():
            self.surface_width, self.surface_height = surf_size
    
        # Insert all our sprites under the provided key
        self._insert_sprites(key, fit_sprites)
        
        # Of course, return the success
        return True
    
    def contains_sprites(self, key: Any) -> bool:
        "Does this atlas contain any sprites under the provided key?"
        return key in self.sprite_map
    
    def push_sprites(self, key: Any, surfaces: tuple[pg.Surface]) -> bool:
        """
        Push a tuple of sprites onto the atlas. This operation can fail however, thus 
        not registering anything to the surface (`True` means success).
        Either all sprites must be fit, or none will be added to the surface under the provided key.
        """

        return self._fit_sprites(
            key, 
            tuple(SpriteRect(surf) for surf in surfaces)
        ) 
    
    def push_sprite(self, key: Any, surface: pg.Surface) -> bool:
        "Essentially the same as `push_sprites`, but for a single sprite"
        return self._fit_sprites(key, (SpriteRect(surface), ))
                
    def get_sprites(self, key: Any) -> Optional[tuple[SpriteRect]]:
        "Try get sprites under the provided key"
        return self.sprite_map.get(key)
    
    def get_sprite(self, key: Any) -> Optional[SpriteRect]:
        "Essentially the same as `get_sprites`, but only requests one sprite"
        sprites = self.get_sprites(key)
        if sprites is not None:
            return sprites[0]
        
    def get_surface(self) -> pg.Surface:
        """
        Render this sprite map onto a surface. This will return a pygame surface.
        Don't call this frequently, as this method doesn't cache the surface!
        """
        surf = pg.Surface((self.surface_width, self.surface_height), pg.SRCALPHA)

        for sprite_rect in chain.from_iterable(self.sprite_map.values()):
            sprite_rect.draw(surf)

        return surf
    
    def consume_added_sprites(self) -> tuple[SpriteRect]:
        "Consume and return all newly added sprites to this atlas"
        ret = tuple(self.new_added_sprites)
        self.new_added_sprites.clear()

        return ret