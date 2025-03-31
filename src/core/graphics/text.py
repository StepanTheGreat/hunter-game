"Text rendering plugin!"

import pygame as pg
import moderngl as gl

from plugin import Plugin, Schedule, Resources
from core.assets import add_loaders
from .ctx import GraphicsContext, DEFAULT_FILTER
from modules.atlas import SpriteAtlas, SpriteRect

DEFAULT_FONT_SIZE = 64

class FontGPU:
    DEFAULT_CHARACTERS = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890_~=\|-?.,><+@!#$%^&*()"
    TEXTURE_LIMIT = 1024

    def __init__(self, ctx: gl.Context, font: pg.font.Font, filter: int = DEFAULT_FILTER):
        self.ctx = ctx
        self.font = font
        self.atlas = SpriteAtlas(ctx, 256, True, FontGPU.TEXTURE_LIMIT, filter)
        
        # Prerender a default character set
        self.load_chars(FontGPU.DEFAULT_CHARACTERS)

    def measure(self, s: str) -> tuple[int, int]:
        "Measure a string"
        return self.font.size(s)
    
    def get_height(self) -> int:
        return self.font.get_height()

    def get_or_insert_char(self, char: str) -> SpriteRect:
        if not self.atlas.contains_sprite(char):
            assert self.push_char(char), "Couldn't fit a character. Maybe hit a texture limit"
                    
        return self.atlas.get_sprite(char)

    def get_char_uvs(self, char: str) -> tuple[float, ...]:
        """
        Fetch or automatically add a rectangle of this character in the font.

        This function returns a rectangle in coordinates between 0 and 1, and is useful solely
        for text rendering
        """
        self.get_or_insert_char(char)
        return self.atlas.get_local_sprite_rect(char)
    
    def get_char_size(self, char: str) -> tuple[int, int]:
        return self.get_or_insert_char(char).get_size()
    
    def push_char(self, char: str) -> bool:
        char_w, char_h = self.measure(char)

        # If a character has a 0 size - we'll make a 1x1 transparent surface for it. 
        # Else we'll just render the character as is
        if char_w == 0 or char_h == 0:
            char_surf = pg.Surface((1, 1), pg.SRCALPHA)
        else:
            char_surf = self.font.render(char, True, (255, 255, 255)) 
        
        return self.atlas.push_sprite(char, char_surf)
    
    def load_chars(self, chars: str):
        for char in chars:
            assert self.push_char(char), "Couldn't fit a character"
    
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

def loader_font_gpu(resources: Resources, path: str, filter: int = DEFAULT_FILTER):
    "A custom loader for GPU fonts"
    gfx = resources[GraphicsContext]
    font_cpu = pg.font.Font(path, DEFAULT_FONT_SIZE)

    return FontGPU(gfx.get_context(), font_cpu, filter)

class TextPlugin(Plugin):
    def build(self, app):
        add_loaders(app, (FontGPU, loader_font_gpu))