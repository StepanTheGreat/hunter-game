"A general purpose 2D renderer. Everything related to UI, 2D text and so on - happens here."

import numpy as np
import moderngl as gl

from plugin import Resources, Plugin, Schedule

from core.assets import AssetManager
from core.graphics import GraphicsContext
from core.graphics.objects import *
from core.graphics.text import FontGPU

RENDERER_PIPELINE_PARAMS = PipelineParams(
    cull_face=False,
    alpha_blending=True,
    depth_test=False
)

RENDERER_VERTEX_ATTRIBUTES = ("position", "uv", "color")

def make_quad(*points: tuple[tuple[float], tuple[float], tuple[float]]) -> DumbMeshCPU:
    p1, p2, p3, p4 = points
    return DumbMeshCPU(
        np.array([
            *p1[0],   *p1[1],  *p1[2],
            *p2[0],   *p2[1],  *p2[2],
            *p3[0],   *p3[1],  *p3[2],
            *p4[0],   *p4[1],  *p4[2],
        ], dtype=np.float32),
        np.array([0, 1, 2, 1, 2, 3], dtype=np.uint32)
    )

class DrawCall:
    """
    A single draw call is a combination of geometry and texture. 
    Draw calls can merge if their texture is the same
    """
    def __init__(self, mesh: DumbMeshCPU, texture: gl.Texture):
        self.mesh = mesh
        self.texture = texture

class DrawCallBatch:
    "Draw call container and merger"
    def __init__(self, verticies: int, indicies: int):
        self.reserved_mesh = ReservedMeshCPU(verticies, indicies)
        self.texture = None

    def can_merge(self, draw_call: DrawCall):
        # Only compatible if it can both fit its geometry and have the same texture
        # OR, if the texture is simply not set
        return (
            self.reserved_mesh.can_fit_mesh(draw_call.mesh) 
            and (self.texture is None or self.texture == draw_call.texture)
        )
    
    def merge_draw_call(self, draw_call: DrawCall):
        assert self.can_merge(draw_call)

        self.reserved_mesh.push_mesh(draw_call.mesh)
        if self.texture is None:
            self.texture = draw_call.texture

    def get_geometry(self) -> tuple[np.ndarray, np.ndarray]:
        "Get the actual geometry of this batch (i.e. without uninitialized array garbage)"
        return self.reserved_mesh.get_verticies(), self.reserved_mesh.get_indices()

    def reset(self):
        self.reserved_mesh.clear()
        self.texture = None

class Renderer2D:
    def __init__(self, gfx: GraphicsContext, assets: AssetManager, vertex_elements: int, index_elements: int, max_draw_calls: int):
        self.ctx = gfx.get_context()
        self.white_texture = gfx.get_white_texture()

        self.vertex_elements = vertex_elements
        self.index_elements = index_elements
        self.max_draw_calls = max_draw_calls

        self.dc_batches: list[DrawCallBatch] = [DrawCallBatch(vertex_elements, index_elements) for _ in range(self.max_draw_calls)]
        self.dc_ptr = 0

        self.pipeline = Pipeline(
            self.ctx, 
            assets.load(gl.Program, "shaders/2d"),
            RENDERER_PIPELINE_PARAMS,
            RENDERER_VERTEX_ATTRIBUTES
        )

        self.vbo = self.ctx.buffer(reserve=vertex_elements, dynamic=True)
        self.ibo = self.ctx.buffer(reserve=index_elements, dynamic=True)
        self.vao = self.ctx.vertex_array(
            self.pipeline.program, 
            self.vbo, 
            *self.pipeline.vertex_attributes,
            index_buffer=self.ibo
        )

    def push_draw_call(self, draw_call: DrawCall):
        batch = self.dc_batches[self.dc_ptr]

        if batch.can_merge(draw_call):
            batch.merge_draw_call(draw_call)
        else:
            self.dc_ptr += 1
            assert self.dc_ptr < self.max_draw_calls, f"Reached a 2D draw call limit of {self.max_draw_calls}"
            self.dc_batches[self.dc_ptr].merge_draw_call(draw_call)

    def reset_draw_call_batches(self):
        """
        Resetting means setting their internal pointers to zero and setting textures to `None`.
        
        Nothing is actually cleared, and all batches will get reused again
        """
        for batch in self.dc_batches[:self.dc_ptr+1]:
            batch.reset()
            
        self.dc_ptr = 0

    def draw_rect(self, rect: tuple[int, ...], color: tuple[float, ...]):
        x, y, w, h = rect
        r, g, b = color
        rect_mesh = make_quad(
            ((x, y), (0, 0), (r, g, b)),
            ((x+w, y), (1, 0), (r, g, b)),
            ((x, y+h), (0, 1), (r, g, b)),
            ((x+w, y+h), (1, 1), (r, g, b)),
        )
        self.push_draw_call(DrawCall(rect_mesh, self.white_texture))

    def draw_text(self, font: FontGPU, text: str, pos: tuple[int], color: tuple[float], size: float):
        x, y = pos
        x_offset = 0
        for char in text:
            uvx, uvy, uvw, uvh = font.get_char_uvs(char)
            cw, ch = font.get_char_size(char)
            cw, ch = cw*size, ch*size
            lx = x+x_offset

            self.push_draw_call(DrawCall(make_quad(
                ((lx,    y),    (uvx,     uvy+uvh), color),
                ((lx+cw, y),    (uvx+uvw, uvy+uvh), color),
                ((lx,    y+ch), (uvx,     uvy),     color),
                ((lx+cw, y+ch), (uvx+uvw, uvy),     color)

            ), font.get_texture()))

            x_offset += cw

    def issue_draw_call_batches(self, projection: np.ndarray):
        "Render everything with the provided projection matrix and reset the draw batches"

        self.pipeline["projection"] = projection
        
        self.pipeline.apply_params()
        for draw_batch in self.dc_batches[:self.dc_ptr+1]:
            verticies, indices = draw_batch.get_geometry()

            self.vbo.write(verticies)
            self.ibo.write(indices)

            vertex_elements = len(indices)

            draw_batch.texture.use()
            self.vao.render(vertices=vertex_elements)

        self.reset_draw_call_batches()

__my_test_font = None

def create_renderer(resources: Resources):
    assets = resources[AssetManager]
    gfx = resources[GraphicsContext]

    resources.insert(Renderer2D(gfx, assets, 5000, 1000, 64))

    import pygame as pg

    f = pg.font.SysFont("bold", 60)
    global __my_test_font
    __my_test_font = FontGPU(gfx.get_context(), f)


def draw_rect(resources: Resources):
    renderer = resources[Renderer2D]
    renderer.draw_rect((-0.5, -0.5, 0.5, 0.5), (1, 0, 0))
    renderer.draw_rect((0.5, -0.5, 0.5, 0.5), (1, 1, 0))

    global __my_test_font

    renderer.draw_text(__my_test_font, "Testing...", (-0.8, 0.3), (1, 0, 0), 0.005)

def issue_draw_calls(resources: Resources):
    resources[Renderer2D].issue_draw_call_batches(np.identity(4).flatten())

class RendererPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Startup, create_renderer)
        app.add_systems(Schedule.Render, draw_rect)
        app.add_systems(Schedule.PostRender, issue_draw_calls)