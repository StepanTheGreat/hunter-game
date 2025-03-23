"Text rendering plugin!"

import pygame as pg
import moderngl as gl

from plugin import Plugin, Schedule, Resources
from core.assets import AssetManager, add_loaders
from core.graphics import GraphicsContext
from modules.atlas import SpriteAtlas, SpriteRect

DEFAULT_FONT_SIZE = 32

class FontGPU:
    DEFAULT_CHARACTERS = ""
    TEXTURE_LIMIT = 512

    def __init__(self, ctx: gl.Context, font: pg.Font):
        self.ctx = ctx
        self.font = font
        self.atlas = SpriteAtlas(256, True, FontGPU.TEXTURE_LIMIT)
        
        # Prerender a default character set
        self.load_chars(FontGPU.DEFAULT_CHARACTERS)

    def get_char(self, char: str) -> tuple[float, ...]:
        """
        Fetch or automatically add a rectangle of this character in the font.

        This function returns a rectangle in coordinates between 0 and 1, and is useful solely
        for text rendering
        """
        rect = self.atlas.get_local_sprite_rect(char)
        if rect is None:
            assert self.atlas.push_sprite(char), "Couldn't fit a sprite. Maybe hit a texture limit"
            rect = self.atlas.get_local_sprite_rect(char)

        return rect
    
    def load_chars(self, chars: str):
        for char in chars:
            self.atlas.push_sprite(char, self.font.render(char, False, (255, 255, 255)))
    
    def get_texture(self) -> gl.Texture:
        """
        Get the font's texture. 
        
        This is an expensive operation if the font's characters change frequently.
        Make sure to preload them in advance using the `load_chars` method
        """
        return self.atlas.get_texture()

    def release(self):
        "Free the GPU resources for this font atlas"
        self.atlas.release()

def loader_font_gpu(resources: Resources, path: str, size: int = DEFAULT_FONT_SIZE):
    "A custom loader for GPU fonts"
    gfx = resources[GraphicsContext]
    font_cpu = pg.font.Font(path, size)

    return FontGPU(gfx.get_context(), font_cpu)

class TextPlugin(Plugin):
    def build(self, app):
        add_loaders(app, (FontGPU, loader_font_gpu))