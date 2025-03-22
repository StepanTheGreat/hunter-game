"A core module responsible for everything related to graphics, geometry and so on"

import pygame as pg
import moderngl as gl

from plugin import Plugin, Schedule
from plugin import Resources

from .objects import *
from .batch import * 

CLEAR_COLOR = (0, 0, 0, 1)

def make_texture(ctx: gl.Context, surf: pg.Surface) -> gl.Texture:
    "Create a GPU texture from a CPU surface"
    return ctx.texture(surf.get_size(), surf.get_bytesize(), surf.get_view("1"))

def make_white_texture(ctx: gl.Context) -> gl.Texture:
    "Generate a white pixel GPU texture"
    "Generate a 1x1 white picture. Highly useful for reusing shaders for color/texture meshes"
    white_surf = pg.Surface((1, 1), pg.SRCALPHA)
    white_surf.fill((255, 255, 255, 255))
    return make_texture(ctx, white_surf)

class GraphicsPlugin(Plugin):
    "A plugin responsible for managing a ModernGL context"

    "A graphics plugin responsible for storing the graphics context and clearing the screen"
    def build(self, app):
        app.insert_resource(GraphicsContext())
        app.add_systems(Schedule.PreRender, clear_screen)

class GraphicsContext:
    "The global ModernGL"
    def __init__(self):
        self.ctx: gl.Context = gl.get_context()
        self.white_texture: gl.Texture = make_white_texture(self.ctx)
    
    def get_white_texture(self) -> gl.Texture:
        return self.white_texture
    
    def get_context(self) -> gl.Context:
        return self.ctx
        
    def clear(self, color: tuple[int, ...]):
        self.ctx.clear(*color)

def clear_screen(resources: Resources):
    resources[GraphicsContext].clear(CLEAR_COLOR)