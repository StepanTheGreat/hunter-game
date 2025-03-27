"A general purpose 2D renderer. Everything related to UI, 2D text and so on - happens here."

import numpy as np
import moderngl as gl

from plugin import Resources, Plugin, Schedule

from core.assets import AssetManager
from .ctx import GraphicsContext
from .text import FontGPU
from .objects import *
from .camera import othorgaphic_matrix

from app_config import CONFIG

VERTEX_ELEMENTS = 5000
INDEX_ELEMENTS = 1000
MAX_DRAW_CALLS = 32

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

def make_circle(pos: tuple[float, float], radius: float, color: tuple[float, ...], points: int = 20) -> DumbMeshCPU:
    assert points > 2, "Can't build a circle mesh with less than 3 points" 
    assert radius > 0, "Why?"
    
    x, y = pos
    r = radius

    verticies = np.empty((points, 7), dtype=np.float32)
    indices = np.empty((points-2, 3), dtype=np.uint32)
    
    angle = 0
    dt_angle = (np.pi*2)/points
    for point in range(points):
        verticies[point] = np.array([
            x+np.cos(angle)*r, y+np.sin(angle)*r, 0, 0, *color
        ])
        angle += dt_angle

    for ind in range(1, points-1):
        indices[ind-1] = np.array([0, ind, ind+1])

    return DumbMeshCPU(verticies.flatten(), indices.flatten())

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
    """
    A renderer is a 2D batcher for dynamic geometry. It's not as efficient as rendering static geometry (since
    sending geometry every frame to the GPU iis slow) - it's still an awesome tool for dynamic things like 
    GUI, text, shapes and much more.
    """
    def __init__(self, gfx: GraphicsContext, assets: AssetManager, vertex_elements: int, index_elements: int, max_draw_calls: int):
        self.ctx = gfx.get_context()
        self.white_texture = gfx.get_white_texture()

        self.vertex_elements = vertex_elements
        self.index_elements = index_elements
        self.max_draw_calls = max_draw_calls

        self.dc_batches: list[DrawCallBatch] = [DrawCallBatch(vertex_elements, index_elements) for _ in range(self.max_draw_calls)]
        self.dc_ptr = None

        self.pipeline = Pipeline(
            self.ctx, 
            assets.load(gl.Program, "shaders/2d"),
            RENDERER_PIPELINE_PARAMS,
            RENDERER_VERTEX_ATTRIBUTES
        )

        self.vbo = self.ctx.buffer(reserve=vertex_elements*4, dynamic=True)
        self.ibo = self.ctx.buffer(reserve=index_elements*4, dynamic=True)
        self.vao = self.ctx.vertex_array(
            self.pipeline.program, 
            self.vbo, 
            *self.pipeline.vertex_attributes,
            index_buffer=self.ibo
        )

    def push_draw_call(self, draw_call: DrawCall):
        if self.dc_ptr is None:
            self.dc_ptr = 0
        
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

        self.dc_ptr = None

    def draw_rect(self, rect: tuple[int, ...], color: tuple[float, ...]):
        x, y, w, h = rect
        r, g, b = color
        rect_mesh = make_quad(
            ((x, y),     (0, 1), (r, g, b)),
            ((x+w, y),   (1, 1), (r, g, b)),
            ((x, y+h),   (0, 0), (r, g, b)),
            ((x+w, y+h), (1, 0), (r, g, b)),
        )
        self.push_draw_call(DrawCall(rect_mesh, self.white_texture))

    def draw_circle(self, pos: tuple[float, float], radius: float, color: tuple[float, ...], points: int = 20):
        circle_mesh = make_circle(pos, radius, color, points)
        self.push_draw_call(DrawCall(circle_mesh, self.white_texture))


    def draw_text(self, font: FontGPU, text: str, pos: tuple[int], color: tuple[float], size: float):
        x, y = pos
        x_offset = 0
        for char in text:
            uvx, uvy, uvw, uvh = font.get_char_uvs(char)
            cw, ch = font.get_char_size(char)
            cw, ch = cw*size, ch*size
            lx = x+x_offset

            self.push_draw_call(DrawCall(make_quad(
                ((lx,    y),    (uvx,     uvy),         color),
                ((lx+cw, y),    (uvx+uvw, uvy),         color),
                ((lx,    y+ch), (uvx,     uvy+uvh),     color),
                ((lx+cw, y+ch), (uvx+uvw, uvy+uvh),     color)

            ), font.get_texture()))

            x_offset += cw

    def draw(self, projection: np.ndarray):
        "Render everything with the provided projection matrix and reset the draw batches"

        if self.dc_ptr is None:
            # We have nothing to draw
            return

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

def issue_draw_calls(resources: Resources):
    projection = othorgaphic_matrix(0, CONFIG.width, CONFIG.height, 0, -1, 1)
    resources[Renderer2D].draw(projection)

class RendererPlugin(Plugin):
    def build(self, app):
        app.insert_resource(Renderer2D(
            app.get_resource(GraphicsContext),
            app.get_resource(AssetManager),
            VERTEX_ELEMENTS,
            INDEX_ELEMENTS,
            MAX_DRAW_CALLS
        ))
        app.add_systems(Schedule.PostRender, issue_draw_calls)