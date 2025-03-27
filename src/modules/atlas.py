"A module for batching images and their associated data into bigger images"

import pygame as pg
import moderngl as gl

from core.graphics.ctx import make_texture

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

class SpriteAtlas:
    """
    A sprite atlas is a really primitive sprite batcher. Texture switches are expensive on GPU, so atlasing
    is the most widely used practice to avoid issuing multiple draw calls per every image.

    It essentially fits a lot of smaller rectangles onto a texture, 
    """

    TEXTURE_LIMIT = 2048
    "A reasonable limit on most hardware"

    def __init__(self, ctx: gl.Context, texture_size: int, resizable: bool, texture_limit: int = None):
        self.ctx = ctx

        self.sprite_map: dict[Any, SpriteRect] = {}
        self.resizable = resizable
        self.texture_width: int = texture_size
        self.texture_height: int = texture_size

        self.texture_limit = texture_limit if texture_limit is not None else SpriteAtlas.TEXTURE_LIMIT

        self.is_syncronized = False 
        self.taken_corners = set()

        self.__cached_texture: gl.Texture = None

    def __resize(self):
        "Resize rectangularly. First in x axis, then in y - on repeat"
        if self.texture_width == self.texture_height:
            self.texture_width *= 2
        else:
            self.texture_height *= 2
        self.is_syncronized = False

    def can_resize(self) -> bool:
        "This atlas can resize unless it's of size `TEXTURE_LIMIT`, which is 2048 on most hardware"
        return (
            self.resizable and 
            (self.texture_width < self.texture_limit or self.texture_height < self.texture_limit)
        )

    def __fit_char(self, key: Any, new_sprite: SpriteRect) -> bool:
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
        sprite_rects = list(self.sprite_map.values())

        if len(self.sprite_map) < 1:
            # If the map is empty, simply insert it at coordinates 0, 0
            self.sprite_map[key] = new_sprite
            self.is_syncronized = False
            return True
        else:
            # Else we will need to insert it with other sprites
            while True:
                for existing_rect in sprite_rects:
                    corners = existing_rect.corners(new_sprite.width(), new_sprite.height())
                    for (x, y) in corners:

                        if (x, y) in self.taken_corners:
                            continue
                        elif x >= self.texture_width-new_sprite.width() or y >= self.texture_height-new_sprite.height():
                            continue
                        elif x < 0 or y < 0:
                            continue

                        new_sprite.move(x, y)
                        if not new_sprite.collides(sprite_rects):
                            self.sprite_map[key] = new_sprite
                            self.taken_corners.add((x, y))
                            self.is_syncronized = False
                            return True
                
                if self.can_resize():
                    # TODO: Fix the bug mentioned in the doc string
                    self.__resize()
                else:
                    "Maximum size"
                    return False
    
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
            return self.__fit_char(key, sprite_rect) 
        
        return True
        
    def get_sprite(self, key: Any) -> Optional[SpriteRect]:
        "Try get a sprite under the provided key"
        return self.sprite_map.get(key)
    
    def get_local_sprite_rect(self, key: Any) -> Optional[tuple[float, ...]]:
        """
        A \"local\" sprite rect is a rectangle whose coordinates are in range between 0 and 1. 
        Texture coordinates simply put.
        """

        if (sprite := self.get_sprite(key)):
            x, y, w, h = sprite.get_rect()

            return (
                x/self.texture_width,
                y/self.texture_height,
                w/self.texture_width,
                h/self.texture_height
            )
        
    def get_surface(self) -> pg.Surface:
        """
        Render this sprite map onto a surface. This will return a pygame surface, though you most likely would
        likely want to use the `get_texture` one.
        """
        surf = pg.Surface((self.texture_width, self.texture_height), pg.SRCALPHA)

        for sprite_rect in self.sprite_map.values():
            sprite_rect.draw(surf)

        return surf

    def __sync_texture(self, new_surf: pg.Surface):
        "Syncronize the internal GPU texture with our CPU surface"

        if self.__cached_texture is None:
            # If a texture is not initialized - just make a new one with our data! 

            self.__cached_texture = make_texture(self.ctx, new_surf)
        else:
            # Else we would need to update an existing one

            if self.__cached_texture.width != self.texture_width or self.__cached_texture.height != self.texture_height:
                # Now, if its dimensions are different from our surface - we obviously will have to delete the last one
                # and create a new one

                self.__cached_texture.release()
                self.__cached_texture = make_texture(self.ctx, new_surf)
            else:
                # In any other case, just write our surface data to our texture
                
                self.__cached_texture.write(new_surf.get_view("1"))
        
    def get_texture(self) -> gl.Texture:
        """
        Get a GPU texture of this atlas. Since the atlas is lazy, it will immediately perform all rendering 
        operations if it has changed since last texture. 

        A new texture can absolutely be different from the one issued later, so always use the most recent ones.

        Calling this method frequently isn't expensive since it will cache the texture internally, though it 
        could be if you add new sprites frequently.
        """

        if not self.is_syncronized:
            self.__sync_texture(self.get_surface())
            self.is_syncronized = True

        return self.__cached_texture
    
    def release(self):
        if self.__cached_texture is not None:
            self.__cached_texture.release()