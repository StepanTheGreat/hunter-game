import moderngl as gl
import pygame as pg

from plugin import Plugin, Resources
from math import log2, ceil
from file import load_file_str

from core.graphics.ctx import *
from core.assets import AssetManager, add_loaders

from modules.config import typed_dataclass, load_config, TypedDataclassTypeMismatch
from modules.atlas import SurfaceAtlas, SpriteRect

from typing import Optional, Any, Union

DYNAMIC_ATLAS_MIN_SIZE = (256, 256)
DYNAMIC_ATLAS_MAX_SIZE = 2048

class TextureAtlas:
    """
    A sprite atlas is a really primitive sprite batcher. Texture switches are expensive on GPU, so atlasing
    is the most widely used practice to avoid issuing multiple draw calls per every image.

    It essentially fits a lot of smaller rectangles onto a texture, 
    """

    def __init__(
        self, 
        ctx: gl.Context, 
        texture_size: tuple[int, int], 
        resizable: bool, 
        texture_limit: int, 
        filter: int = DEFAULT_FILTER
    ):
        self.ctx = ctx
        self.atlas = SurfaceAtlas(texture_size, resizable, texture_limit)
        self.filter = filter
        self.texture_limit = texture_limit

        self._cached_texture: gl.Texture = None

    def contains_sprite(self, key: Any) -> bool:
        self.atlas.contains_sprite(key)
    
    def push_sprite(self, key: Any, surf: pg.Surface) -> bool:
        """
        Try fit a surface under the provided key. If successful it will return `True`, and the provided surface
        will get registered under the provided key. If `False`, then nothing will happen to the texture.

        If a sprite is fit however, depends on whether the texture has enough space 
        """

        return self.atlas.push_sprite(key, surf)
        
    def get_sprite(self, key: Any) -> Optional[SpriteRect]:
        "Try get a sprite under the provided key"
        return self.atlas.get_sprite(key)
    
    def get_sprite_texture(self, key: Any) -> Optional[Texture]:
        self._sync_texture()

        if (sprite := self.get_sprite(key)):
            x, y, w, h = sprite.get_rect()

            return Texture(self._cached_texture, (x, y, w, h))

    def _sync_texture(self):
        "Syncronize the internal GPU texture with our CPU surface"

        new_sprites = self.atlas.consume_added_sprites()
        if not new_sprites:
            # No new sprites added, we'll just do nothing
            return
        
        new_surf = self.atlas.get_surface()

        if self._cached_texture is None:
            # If a texture is not initialized - just make a new one with our data! 

            self._cached_texture = make_texture(self.ctx, new_surf, self.filter)
        else:
            # Else we would need to update an existing one
            width, height = new_surf.get_size()
            if self._cached_texture.width != width or self._cached_texture.height != height:
                # Now, if its dimensions are different from our surface - we obviously will have to delete the last one
                # and create a new one

                self._cached_texture.release()
                self._cached_texture = make_texture(self.ctx, new_surf, self.filter)
            else:
                # We're going to find the largest affected region and update it at once
                min_x = min(new_sprites, key=lambda sprite: sprite.rect.x).rect.x
                min_y = min(new_sprites, key=lambda sprite: sprite.rect.y).rect.y
                max_w = max(new_sprites, key=lambda sprite: sprite.rect.x+sprite.rect.w).rect.w
                max_h = max(new_sprites, key=lambda sprite: sprite.rect.y+sprite.rect.h).rect.h

                x, y, w, h = min_x, min_y, max_w, max_h
                self._cached_texture.write(
                    get_surface_gl_data(new_surf.subsurface(x, y, w, h)),
                    viewport=(x, y, w, h)
                )
        
    def get_texture(self) -> gl.Texture:
        """
        Get a GPU texture of this atlas. Since the atlas is lazy, it will immediately perform all rendering 
        operations if it has changed since last texture. 

        A new texture can absolutely be different from the one issued later, so always use the most recent ones.

        Calling this method frequently isn't expensive since it will cache the texture internally, though it 
        could be if you add new sprites frequently.
        """

        self._sync_texture()
        return self._cached_texture
    
    def release(self):
        if self._cached_texture is not None:
            self._cached_texture.release()

@typed_dataclass
class StaticTextureAtlas:
    source: str
    sprites: dict

def _closest_pow2_size(image_size: tuple[int, int]) -> tuple[int, int]:
    """
    For any image size, transform it to the closest possible power-of-2 image size, whose axis
    are power-of-2 axis of the original dimensions.

    ## An example:
    Using an image size `120x400`, neither axis is power-of-2. The point of this algorithm
    is to get the closest texture size, while also using power-of-2 dimensions.

    For `120`, the closest accomodating number is `256`.
    For `400` it's `512`.
    So, as the result - our resulting image size will be `256x512`
    """
    w, h = image_size
    return 2 ** ceil(log2(w)), 2 ** ceil(log2(h))

def _load_static_texture_atlas(
    ctx: gl.Context, 
    assets: AssetManager, 
    atlas: StaticTextureAtlas
) -> TextureAtlas:
    # What we're going to do is SUPER stupid, but I really don't want to optimize this.
    # I think we will just rebuild the entire atlas. Also, we will increase a bit the texture size, since
    # we need power-of-2 textures

    img = pg.image.load(assets.asset_path(atlas.source))

    texture_size = _closest_pow2_size(img.get_size())
    new_atlas = TextureAtlas(ctx, texture_size, False, max(texture_size))

    for sprite_key, sprite_region in atlas.sprites.items():
        assert sprite_region is tuple and len(sprite_region) == 4, "Invalid sprite format used in a static texture atlas"
        (x, y, w, h) = sprite_region

        new_atlas.push_sprite(sprite_key, img.subsurface(x, y, w, h))
    
    return new_atlas

@typed_dataclass
class DynamicTextureAtlas:
    sources: dict

def _load_dynamic_texture_atlas(
    ctx: gl.Context, 
    assets: AssetManager, 
    atlas: DynamicTextureAtlas
) -> TextureAtlas:
    
    # Now, we're going to create the smallest possible base texture, and try fit
    # all sprites onto it

    new_atlas = TextureAtlas(ctx, DYNAMIC_ATLAS_MIN_SIZE, True, DYNAMIC_ATLAS_MAX_SIZE)

    for source_key, source_path in atlas.sources.items():
        assert source_path is str, "Invalid sprite format used in a dynamic texture atlas"

        img = pg.image.load(assets.asset_path(source_path))
        new_atlas.push_sprite(source_key, img)
    
    return new_atlas

def _load_texture_atlas(
    ctx: gl.Context,
    assets: AssetManager, 
    atlas_data: str
) -> TextureAtlas:
    """
    Try guess and load a texture atlas. This function supports 2 types of file atlases:
    - Static (an already built atlas with predefined sprite keys and regions)
    - Dynamic (an atlas that defines sprite keys and source files to batch into an atlas)

    If the format doesn't match anything - will raise an error.
    """
    try:
        atlas = load_config(StaticTextureAtlas, atlas_data)
        return _load_static_texture_atlas(ctx, assets, atlas)
    except TypedDataclassTypeMismatch:
        atlas = load_config(DynamicTextureAtlas, atlas_data)
        return _load_dynamic_texture_atlas(ctx, assets, atlas)

def loader_texture_atlas(resources: Resources, path: str) -> TextureAtlas:
    "A loader for texture atlases"
    atlas_data = load_file_str(path)
    return _load_texture_atlas(
        resources[GraphicsContext].get_context(),
        resources[AssetManager],
        atlas_data
    )

def _get_path_atlas_split(path: str) -> Union[tuple[str, str]]:
    path_file = path.split("/")[-1]
    atlas_texture_split = path_file.split("#")

    if len(atlas_texture_split) == 2:
        # We got an atlas-texture split, so we can return the atlas path and the texture's key
        return atlas_texture_split

def loader_texture(resources: Resources, path: str, filter: int = DEFAULT_FILTER) -> Texture:
    "A custom GPU texture loader from files"

    texture_atlas_split = _get_path_atlas_split(path)
    if texture_atlas_split is None:
        ctx: gl.Context = resources[GraphicsContext].get_context()
        surface = pg.image.load(path)
        return Texture(make_texture(ctx, surface, filter))
    else:
        atlas_path, sprite_key = texture_atlas_split
        return (resources[AssetManager]
            .load(TextureAtlas, atlas_path)
            .get_sprite_texture(sprite_key))
    
class AtlasPlugin(Plugin):
    def build(self, app):
        add_loaders(app,
            (TextureAtlas, loader_texture_atlas),
            (Texture, loader_texture)
        )