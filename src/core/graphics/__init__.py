"A core module responsible for everything related to graphics, geometry and so on"

import pygame as pg
import moderngl as gl

from plugin import Plugin, Schedule
from plugin import Resources

from file import load_file_str
from ..assets import AssetManager

from .objects import *
from .camera import *

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

def loader_shader_program(resources: Resources, path: str) -> gl.Program:
    """
    A custom shader program loader. 

    A cool thing with it is that a path to a shader can be passed without file extensions. This loader 
    will automatically load both the fragment and vertex shader under the same name.
    """

    ctx: gl.Context = resources[GraphicsContext].get_context()

    vertex_shader = load_file_str(path + ".vert")
    fragment_shader = load_file_str(path + ".frag") 

    return ctx.program(vertex_shader, fragment_shader)

def loader_texture(resources: Resources, path: str) -> gl.Program:
    "A custom GPU texture loader from files"
    ctx: gl.Context = resources[GraphicsContext].get_context()
    surface = pg.image.load(path)
    return make_texture(ctx, surface)

class GraphicsContext:
    "The global ModernGL"
    def __init__(self, ctx: gl.Context):
        self.ctx: gl.Context = ctx
        self.white_texture: gl.Texture = make_white_texture(self.ctx)
        
    def get_context(self) -> gl.Context:
        return self.ctx
    
    def get_white_texture(self) -> gl.Texture:
        return self.white_texture
        
    def clear(self, color: tuple[int, ...]):
        self.ctx.clear(*color)

def clear_screen(resources: Resources):
    resources[GraphicsContext].clear(CLEAR_COLOR)

class GraphicsPlugin(Plugin):
    "A plugin responsible for managing a ModernGL context"

    "A graphics plugin responsible for storing the graphics context and clearing the screen"
    def build(self, app):
        app.insert_resource(GraphicsContext(gl.get_context()))
        app.add_systems(Schedule.PreRender, clear_screen)

        # Add asset loaders for textures and shaders
        assets = app.get_resource(AssetManager)
        assets.add_loader(gl.Program, loader_shader_program)
        assets.add_loader(gl.Texture, loader_texture)

        app.add_plugins(CameraPlugin())