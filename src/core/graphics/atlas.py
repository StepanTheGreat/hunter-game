"""
A Texture Atlas is the extension of the Surface Atlas defined in the modules directory (please read it, 
as it explains its sole purpose of existance).

This atlas automatically manages its own OpenGL texture, with a convenient to use interface.
This should be preferred over using normal textures in some cases, as it allows optimizing for draw
calls.

This module also defines a new type of asset - the file atlas. There are 2 types of atlases:
- Dynamic (those that simply reference image paths and then are constructed at runtime)
- Static (those that reference an already built atlas image, and just parse its sprites)

Both of these can be loaded directly using the asset manager.

BUT, this is not all... to simplify asset loading and management, this module also includes a convenient
way of referencing individual textures inside atlases: the `#` separator. Essentially, it's added
at the end of the path, where the key of the referenced texture goes after the separator. For example:
`images/blocks.atl#brick`.
Here, we're referencing the `brick` texture, inside the atlas `blocks.atl`. What this is going to do, is 
automatically load and build the underlying atlas (in this case `images/blocks.atl`), and then retrieve
the `brick` texture from it (if present of course)

The asset manager doesn't care about the file extension of your atlases, so `.atl` extension is for
example only. It simply cares for valid JSON data.

## Formats
Here are JSON formats for every type of atlas:

### Dynamic
Dynamic atlases only reference other images on the file system (relative to the directory of the atlas)

Multiple images can be attached to individual sprite keys, making it possible to define animations
```
{
    "dynamic": true,
    "sources": {
        "individual_sprite": "sprite.png",
        "multi_sprites": [
            "path/to/anim1.png",
            "path/to/anim2.png",
            "path/to/anim3.png"
        ]
    }
}
```

### Static
A static atlas only defines the source atlas image, and its sprites instead reference the absolute
regions of said sprite `(x, y, width, height)`.

As with dynamic atlases, multiple regions can be attached to the same key
```
{
    "dynamic": false,
    "source": "atlas.png",
    "sprites": {
        "individual_sprite": [0, 0, 32, 32],
        "multi_sprites": [
            [0, 32, 16, 16],
            [16, 32, 16, 16],
            [32, 32, 16, 16]
        ]
    }
}
```

One final property is that the current implementation of static atlases simply... rebuilds them from
scratch... So one cool thing this allows us to do, is to simply ignore margins in our source atlases
entirely and let the runtime manage those instead
"""

import moderngl as gl
import pygame as pg

from json import loads
from jsonschema import validate, ValidationError

from os.path import abspath

from plugin import Plugin, Resources
from math import log2, ceil
from file import load_file_str

from core.graphics.ctx import *
from core.assets import AssetManager, add_loaders

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

    def contains_sprites(self, key: Any) -> bool:
        return self.atlas.contains_sprites(key)
    
    def push_sprites(self, key: Any, surfaces: tuple[pg.Surface]) -> bool:
        """
        Try fit a surface under the provided key. If successful it will return `True`, and the provided surface
        will get registered under the provided key. If `False`, then nothing will happen to the texture.

        If a sprite is fit however, depends on whether the texture has enough space 
        """

        return self.atlas.push_sprites(key, surfaces)
        
    def get_sprites(self, key: Any) -> Optional[tuple[SpriteRect]]:
        "Try get a sprite under the provided key"
        return self.atlas.get_sprites(key)
    
    def get_sprite_textures(self, key: Any) -> Optional[tuple[Texture]]:
        self._sync_texture()

        if self.atlas.contains_sprites(key):
            return tuple(
                Texture(self._cached_texture, sprite.get_rect()) 
                for sprite in self.get_sprites(key)
            )
    
    def get_sprite_texture(self, key: Any) -> Optional[Texture]:
        self._sync_texture()

        if self.atlas.contains_sprites(key):
            return Texture(self._cached_texture, self.atlas.get_sprite(key).get_rect())

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

ATLAS_JSON_SCHEMA = {
    "properties": {
        # This property tells us of which type this atlas is
        "dynamic": {"type": "boolean"}
    },

    # Now, we're going to perform a check based on the value of `dynamic`
    # Depending on the resulting value, we will expect different rules
    "if": {

        # Essentially, `if dynamic == True`
        "properties": { "dynamic": {"const": True}} 
    },
    "then": {
        # If true, we would like to expect a dictionary `sources`, keys of which are sprite names
        # and values are image paths. It is however possible to also use an array of images per key.

    	"properties": {
        	"sources": {
                "type": "object",
                "additionalProperties": {

                    # Either a single path string or an array of path strings
                    "anyOf": [
                        {"type": "string"},
                        {
                            "type": "array", 
                            "items": {"type": "string"},
                        },
                    ]
                }
            }  
        },

        # Of course it is required
        "required": ["sources"]
    },
    "else": {
        # In any other case our schema will source based on an image. Values in this case of dictionary
        # `sprites` will be rectangles defining areas of the image. As with the previous case, it's
        # possible to use arrays of image regions as sprite values

    	"properties": {
            # The source path of the image
          	"source": {"type": "string"},
              
            # The sprite regions of that image
        	"sprites": {
                "type": "object",
                "additionalProperties": {

                    # Either a 4-value int array (a region rectangle), or an unlimited array of 
                    # said region rectangles
                    "anyOf": [
                        {
                            "type": "array", 
                            "items": {"type": "number"},
                            "minItems": 4, 
                            "maxItems": 4
                        },
                        {
                            "type": "array", 
                            "items": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 4, 
                            "maxItems": 4
                            },
                        },
                    ]
                }
            } 
        },

        # Make both required of course
        "required": ["source", "sprites"]
    },

    # And the dynamic attribute as well!
    "required": ["dynamic"],
}
"""
To explain this monstrosity... This is a JSON schema, and it allows us to validate arbitrary
JSON objects against a specific schema or ruleset. I'm not going to explain the format here, but it's
explained 
"""

def _load_static_texture_atlas(
    ctx: gl.Context, 
    assets: AssetManager, 
    atlas_dir: str,
    atlas: dict
) -> TextureAtlas:
    # What we're going to do is SUPER stupid, but I really don't want to optimize this.
    # I think we will just rebuild the entire atlas. Also, we will increase a bit the texture size, since
    # we need power-of-2 textures

    atlas_source: str = atlas["source"]
    sprites: dict[str, Union[
        tuple[int, int, int, int], 
        tuple[tuple[int, int, int, int]]
    ]] = atlas["sprites"]
    img = pg.image.load(atlas_dir+atlas_source)

    texture_size = _closest_pow2_size(img.get_size())
    new_atlas = TextureAtlas(ctx, texture_size, False, max(texture_size))

    for sprite_key, entry in sprites.items():
        is_list = type(entry[0]) is list

        regions: tuple[tuple[int, int, int, int]] = None
        # Because a single key can define multiple regions - we're managing this separately
        if is_list:
            sprite_regions = entry
            regions = sprite_regions
        else:
            sprite_region = entry
            regions = (sprite_region, )

        sub_surfaces = tuple(img.subsurface(x, y, w, h) for (x, y, w, h) in regions)
        new_atlas.push_sprites(sprite_key, sub_surfaces)
    
    return new_atlas

def _load_dynamic_texture_atlas(
    ctx: gl.Context, 
    atlas_dir: str,
    atlas: dict
) -> TextureAtlas:
    sources: dict[str, Union[str, tuple[str]]] = atlas["sources"]

    new_atlas = TextureAtlas(ctx, DYNAMIC_ATLAS_MIN_SIZE, True, DYNAMIC_ATLAS_MAX_SIZE)

    for source_key, entry in sources.items():
        is_list = type(entry) is list

        if is_list:
            source_paths = entry
            sources = source_paths
        else:
            source_path = entry
            sources = (source_path, )

        imgs = tuple(pg.image.load(atlas_dir+source_path) for source_path in sources)
        new_atlas.push_sprites(source_key, imgs)
    
    return new_atlas

def _load_texture_atlas(
    ctx: gl.Context,
    assets: AssetManager, 
    atlas_dir: str,
    atlas_data: str
) -> TextureAtlas:
    """
    Try guess and load a texture atlas. This function supports 2 types of file atlases:
    - Static (an already built atlas with predefined sprite keys and regions)
    - Dynamic (an atlas that defines sprite keys and source files to batch into an atlas)

    If the format doesn't match anything - will raise an error.
    """
    atlas_obj = loads(atlas_data)

    validate(atlas_obj, ATLAS_JSON_SCHEMA)

    if atlas_obj["dynamic"]:
        return _load_dynamic_texture_atlas(ctx, atlas_dir, atlas_obj)
    else:
        return _load_static_texture_atlas(ctx, assets, atlas_dir, atlas_obj)

def loader_texture_atlas(resources: Resources, path: str) -> TextureAtlas:
    "A loader for texture atlases"
    atlas_data = load_file_str(path)
    atlas_dir = abspath(path + "/../")+"/" # Yup, I know, it's not the best way, but it's a simple one

    try:
        return _load_texture_atlas(
            resources[GraphicsContext].get_context(),
            resources[AssetManager],
            atlas_dir,
            atlas_data
        )
    except ValidationError as e:
        print(f"Failed to parse atlas at \"{path}\":")
        raise e

def _get_path_atlas_split(path: str) -> Union[str, None]:
    atlas_texture_split = path.split("#")

    assert len(atlas_texture_split) <= 2, "Incorrect atlas referencing. Only 1 # can be used"

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
            .load_abs(TextureAtlas, atlas_path)
            .get_sprite_texture(sprite_key))
    
class AtlasPlugin(Plugin):
    def build(self, app):
        add_loaders(app,
            (TextureAtlas, loader_texture_atlas),
            (Texture, loader_texture)
        )