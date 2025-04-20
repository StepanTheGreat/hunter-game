
import pygame as pg
import moderngl as gl

from plugin import Plugin, Schedule
from plugin import Resources

from file import load_file_str
from ..assets import add_loaders

from .objects import *
from .camera import *

CLEAR_COLOR = (0, 0, 0, 1)
DEFAULT_FILTER = gl.NEAREST

def make_texture(ctx: gl.Context, surf: pg.Surface, filter: int = DEFAULT_FILTER) -> gl.Texture:
    "Create a GPU texture from a CPU surface"
    bytesize = surf.get_bytesize()
    format = "RGBA" if bytesize == 4 else "RGB"
    texture = ctx.texture(surf.get_size(), bytesize, pg.image.tostring(surf, format, False))
    texture.filter = (filter, filter)
    return texture

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

def loader_texture(resources: Resources, path: str, filter: int = DEFAULT_FILTER) -> gl.Program:
    "A custom GPU texture loader from files"
    ctx: gl.Context = resources[GraphicsContext].get_context()
    surface = pg.image.load(path)
    return make_texture(ctx, surface, filter)

class GraphicsContext:
    "The global ModernGL"
    def __init__(self, ctx: gl.Context):
        self.ctx: gl.Context = ctx
        self.white_texture: gl.Texture = make_white_texture(self.ctx)

    def update_viewport(self, new_width: int, new_height: int):
        self.ctx.viewport = (0, 0, new_width, new_height)
        
    def get_context(self) -> gl.Context:
        return self.ctx
    
    def get_white_texture(self) -> gl.Texture:
        return self.white_texture
        
    def clear(self, color: tuple[int, ...]):
        self.ctx.clear(*color)

def clear_screen(resources: Resources):
    resources[GraphicsContext].clear(CLEAR_COLOR)

def update_viewport(resources: Resources, event: WindowResizeEvent):
    resources[GraphicsContext].update_viewport(event.new_width, event.new_height)

class GraphicsContextPlugin(Plugin):
    def build(self, app):
        app.insert_resource(GraphicsContext(gl.get_context()))
        app.add_systems(Schedule.PreDraw, clear_screen)

        app.add_event_listener(WindowResizeEvent, update_viewport)

        # Add asset loaders for textures and shaders
        add_loaders(
            app,
            (gl.Program, loader_shader_program),
            (gl.Texture, loader_texture) 
        )