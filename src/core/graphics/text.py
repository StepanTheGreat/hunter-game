"Text rendering plugin!"

import pygame as pg
import moderngl as gl

from plugin import Plugin, Resources
from core.assets import add_loaders
from .ctx import GraphicsContext, DEFAULT_FILTER, Texture
from .atlas import TextureAtlas, SpriteRect

DEFAULT_FONT_SIZE = 64
DEFAULT_CHARACTERS = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890_~=\|-?.,><+@!#$%^&*() "

FONT_MIN_TEXTURE_SIZE = (256, 256)
FONT_MAX_TEXTURE_SIZE = 2048

class FontGPU:
    def __init__(self, ctx: gl.Context, font: pg.font.Font, filter: int = DEFAULT_FILTER):
        self.ctx = ctx
        self.font = font
        self.atlas = TextureAtlas(ctx, FONT_MIN_TEXTURE_SIZE, True, FONT_MAX_TEXTURE_SIZE, filter)
        
        # Prerender a default character set
        self.load_chars(DEFAULT_CHARACTERS)

    def measure(self, s: str) -> tuple[int, int]:
        "Measure a string"
        return self.font.size(s)
    
    def get_height(self) -> int:
        return self.font.get_height()

    def get_or_insert_char(self, char: str) -> SpriteRect:
        if not self.atlas.contains_sprites(char):
            assert self.push_char(char), "Couldn't fit a character"
                    
        return self.atlas.get_sprites(char)[0]

    def get_char_texture(self, char: str) -> Texture:
        """
        Fetch or automatically add a rectangle of this character in the font.

        This function returns a rectangle in coordinates between 0 and 1, and is useful solely
        for text rendering
        """
        if not self.contains_char(char):
            self.get_or_insert_char(char)
        return self.atlas.get_sprite_texture(char)
    
    def get_char_size(self, char: str) -> tuple[int, int]:
        return self.get_or_insert_char(char).get_size()
    
    def contains_char(self, char: str) -> bool:
        return self.atlas.contains_sprites(char)
    
    def push_char(self, char: str) -> bool:
        char_w, char_h = self.measure(char)

        # If a character has a 0 size - we'll make a 1x1 transparent surface for it. 
        # Else we'll just render the character as is
        if char_w == 0 or char_h == 0:
            char_surf = pg.Surface((1, 1), pg.SRCALPHA)
        else:
            char_surf = self.font.render(char, True, (255, 255, 255)) 
        
        return self.atlas.push_sprites(char, (char_surf, ))
    
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