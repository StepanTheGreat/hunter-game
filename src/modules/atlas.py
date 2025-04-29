"A module for batching images and their associated data into bigger images"

import pygame as pg
from typing import Any, Optional

class SpriteRect:
    "An individual sprite image. It contains both the image surface and its rectangle"
    def __init__(self, surf: pg.Surface):
        self.surf = surf
        self.rect = self.surf.get_rect()

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
            (x-target_w-1, y) # top-left
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
    if width == height:
        width *= 2
    else:
        height *= 2

    return width, height

class SurfaceAtlas:
    "A CPU surface atlas"
    def __init__(self, surface_size: tuple[int, int], resizable: bool, surface_limit: int):
        self.sprite_map: dict[Any, SpriteRect] = {}
        self.resizable = resizable
        self.surface_width: int = surface_size[0]
        self.surface_height: int = surface_size[1]

        self.surface_limit = surface_limit
        self.taken_corners = set()

        self.new_added_sprites: list[Any] = []

    def _can_scale(self, size: tuple[int, int]) -> bool:
        return (
            self.resizable and 
            (size[0] < self.surface_limit or size[1] < self.surface_limit)
        )

    def can_resize(self) -> bool:
        "This atlas can resize unless it's of size of `surface_limit`"
        return self._can_scale(self.surface_width, self.surface_height)
    
    def _insert_sprite(self, key: Any, new_sprite: SpriteRect, corner_pos: tuple[int, int]):
        """
        Insert the provided sprite into the sprite map, update the newly added sprites, and if
        corner position isn't `None` - will also insert the corner position in the taken corners set.
        """
        self.sprite_map[key] = new_sprite
        self.new_added_sprites.append(new_sprite)

        if corner_pos is not None:
            self.taken_corners.add(corner_pos)

    def get_size(self) -> tuple[int, int]:
        return self.surface_width, self.surface_height

    def _fit_sprite(self, key: Any, new_sprite: SpriteRect) -> bool:
        """
        The algorithm here is extremely simple: for every rectangle we already have in the map - we will iterate
        its corners, and check if our rectangle collides with any other rectangles. It isn't the best algorithm
        for fitting of course, but it's extremely simple and efficient.

        Additional speedup is made by storing all already used corners in a set, thus we will avoid checking
        collisions for those entirely.

        One existing bug with the current implementation though (not related to the algorithm) is that if a key
        can't be fit - we will resize the texture, but won't resize it back.
        In the future, only when a sprite is able to get fit - we will actually change our rectangle's dimensions.
        """
        sprite_rects = tuple(self.sprite_map.values())

        surf_size = self.get_size()

        fit_sprite: tuple[Any, SpriteRect, None] = None

        if len(self.sprite_map) < 1:
            # If the map is empty, simply insert it at coordinates 0, 0
            fit_sprite = (key, new_sprite, None)
            # A possible bug is the sprite being too large, thus not fitting in the initial
            # capacity!
        else:
            # Else we will need to insert it with other sprites
            while not fit_sprite:
                for existing_rect in sprite_rects:
                    corners = existing_rect.corners(new_sprite.width(), new_sprite.height())
                    for (x, y) in corners:                        
                        if (x, y) in self.taken_corners:
                            continue
                        elif x >= surf_size[0]-new_sprite.width() or y >= surf_size[1]-new_sprite.height():
                            continue
                        elif x < 0 or y < 0:
                            continue

                        new_sprite.move(x, y)
                        if not new_sprite.collides(sprite_rects):
                            fit_sprite = (key, new_sprite, (x, y))
                            break
                    
                    if fit_sprite:
                        # An early break in case we did find the sprite
                        break
                
                if self._can_scale(surf_size):
                    # TODO: Fix the bug mentioned in the doc string
                    surf_size = scale_dimensions(surf_size)
                else:
                    # Maximum size
                    break
        
        if fit_sprite:
            self._insert_sprite(*fit_sprite)

            if surf_size != self.get_size():
                self.surface_width, self.surface_height = surf_size
        
        return fit_sprite is not None
    
    def contains_sprite(self, key: Any) -> bool:
        return key in self.sprite_map
    
    def push_sprite(self, key: Any, surf: pg.Surface) -> bool:
        """
        Try fit a surface under the provided key. If successful it will return `True`, and the provided surface
        will get registered under the provided key. If `False`, then nothing will happen to the texture.

        If a sprite is fit however, depends on whether the texture has enough space 
        """

        if key not in self.sprite_map:
            sprite_rect = SpriteRect(surf)
            return self._fit_sprite(key, sprite_rect) 
        
        return True
        
    def get_sprite(self, key: Any) -> Optional[SpriteRect]:
        "Try get a sprite under the provided key"
        return self.sprite_map.get(key)
    
    def get_sprite_uv_rect(self, key: Any) -> Optional[tuple[float, ...]]:
        """
        A \"local\" sprite rect is a rectangle whose coordinates are in range between 0 and 1. 
        Texture coordinates simply put.
        """

        if (sprite := self.get_sprite(key)):
            x, y, w, h = sprite.get_rect()

            return (
                x/self.surface_width,
                y/self.surface_height,
                w/self.surface_width,
                h/self.surface_height
            )
        
    def get_surface(self) -> pg.Surface:
        """
        Render this sprite map onto a surface. This will return a pygame surface.
        Don't call this frequently, as this method doesn't cache the surface!
        """
        surf = pg.Surface((self.surface_width, self.surface_height), pg.SRCALPHA)

        for sprite_rect in self.sprite_map.values():
            sprite_rect.draw(surf)

        return surf
    
    def consume_added_sprites(self) -> tuple[SpriteRect]:
        "Consume and return all newly added sprites to this atlas"
        ret = tuple(self.new_added_sprites)
        self.new_added_sprites.clear()

        return ret