
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

def get_surface_gl_data(surf: pg.Surface) -> bytes:
    "Get openGL compatible pixel data from a pygame surface"
    format = "RGBA" if surf.get_bytesize() == 4 else "RGB"
    return pg.image.tostring(surf, format, False)

def make_texture(ctx: gl.Context, surf: pg.Surface, filter: int = DEFAULT_FILTER) -> gl.Texture:
    "Create a GPU texture from a CPU surface"
    texture = ctx.texture(surf.get_size(), surf.get_bytesize(), get_surface_gl_data(surf))
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

class Texture:
    """
    A texture handle for both GL texture and the texture's region. The purpose of this
    structure is to just simplify data passing. When referencing texture regions from say 
    atlases - it's not convenient to always pass around these UV coordinates.
    For ordinary textures however, we can always set the region to just (0, 0, 1, 1), so it
    acts absolutely identically.

    Additionally, the user doesn't need to import `Texture` from `moderngl` to access the texture - just
    `core.graphics`.
    """
    def __init__(self, texture: gl.Texture, region: tuple[int, int, int, int] = None):
        self.texture: gl.Texture = texture
        "The underlying opengl texture"
        self.region: tuple[int, int, int, int] = (0, 0, texture.width, texture.height) if region is None else region
        "The absolute region referenced by this texture. The minimum is 0, and the maximum is 1"

class GraphicsContext:
    "The global ModernGL"
    def __init__(self, ctx: gl.Context):
        self.ctx: gl.Context = ctx
        self.white_texture: Texture = Texture(make_white_texture(self.ctx), (0, 0, 0, 0))

    def update_viewport(self, new_width: int, new_height: int):
        self.ctx.viewport = (0, 0, new_width, new_height)
        
    def get_context(self) -> gl.Context:
        return self.ctx
    
    def get_white_texture(self) -> Texture:
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

        # Add asset loader for shaders
        add_loaders(
            app,
            (gl.Program, loader_shader_program)
        )