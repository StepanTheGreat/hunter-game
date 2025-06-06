"A general purpose 2D renderer. Everything related to UI, 2D text and so on - happens here."

import numpy as np
import moderngl as gl

from plugin import Resources, Plugin, Schedule

from core.telemetry import Telemetry
from core.assets import AssetManager
from core.graphics import *

MAX_VERTICIES = 10000
MAX_INDICES = 15000
MAX_DRAW_CALLS = 32

RENDERER_PIPELINE_PARAMS = PipelineParams(
    cull_face=False,
    alpha_blending=True,
    depth_test=False
)

RENDERER_VERTEX_ATTRIBUTES = ("position", "uv", "color")
RENDERER_VERTEX_DTYPE = np.dtype([
    ("position", "i2", 2),
    ("uv", "u2", 2),
    ("color", "u1", 3),
    ("_padding", "u1")
])
RENDERER_VERTEX_GL_FORMAT = "2i2 2u2 3f1 x"

PADDING = 0
"""
Because hardware accelerated graphics like power-of-2 aligned data - we're required to align it.
I'm only making this constant so that it will be clear why I'm putting 0s all over 2D vertex data
"""

def make_quad(*points: tuple[tuple[float], tuple[float], tuple[float]]) -> DynamicMeshCPU:
    p1, p2, p3, p4 = points
    return DynamicMeshCPU(
        np.array([
            (p1[0], p1[1],  p1[2], PADDING),
            (p2[0], p2[1],  p2[2], PADDING),
            (p3[0], p3[1],  p3[2], PADDING),
            (p4[0], p4[1],  p4[2], PADDING),
        ], dtype=RENDERER_VERTEX_DTYPE),
        np.array([0, 1, 2, 1, 2, 3], dtype=np.uint32),
        RENDERER_VERTEX_DTYPE
    )

def make_quads(quads: list[tuple[tuple[float], tuple[float], tuple[float]]]) -> DynamicMeshCPU:
    "A more efficient version of `make_quad`, but for generating multiple quads at the same time"

    quads_len = len(quads)

    verticies = np.zeros((quads_len, 4), dtype=RENDERER_VERTEX_DTYPE)
    indices = np.zeros((quads_len, 6), dtype=np.uint32)

    lind = 0
    for ind, quad in enumerate(quads):
        p1, p2, p3, p4 = quad

        verticies[ind] = [
            (p1[0],   p1[1],  p1[2], PADDING),
            (p2[0],   p2[1],  p2[2], PADDING),
            (p3[0],   p3[1],  p3[2], PADDING),
            (p4[0],   p4[1],  p4[2], PADDING),
        ]
        indices[ind] = [lind, lind+1, lind+2, lind+1, lind+2, lind+3]
        lind += 4
    
    return DynamicMeshCPU(verticies.ravel(), indices.ravel(), RENDERER_VERTEX_DTYPE)

def make_circle(pos: tuple[float, float], radius: float, color: tuple[float, ...], points: int = 20) -> DynamicMeshCPU:
    assert points > 2, "Can't build a circle mesh with less than 3 points" 
    assert radius > 0, "Why?"
    
    x, y = pos
    r = radius

    verticies = np.empty(points, dtype=RENDERER_VERTEX_DTYPE)
    indices = np.empty((points-2, 3), dtype=np.uint32)
    
    angle = 0
    dt_angle = (np.pi*2)/points
    for point in range(points):
        verticies[point] = (
            (x+np.cos(angle)*r, y+np.sin(angle)*r), (0, 0), color, PADDING
        )
        angle += dt_angle

    for ind in range(1, points-1):
        indices[ind-1] = [0, ind, ind+1]

    return DynamicMeshCPU(verticies.flatten(), indices.flatten(), RENDERER_VERTEX_DTYPE)

def make_circles(
    circles: tuple[tuple[tuple[float, float], float, tuple[int, ...]]],
    points: int = 20
) -> DynamicMeshCPU:
    "A more efficient version of `make_circle`, but for batching A LOT of circles"

    assert points > 2, "Can't build a circle mesh with less than 3 points" 
    
    circles_len = len(circles)

    verticies = np.empty(circles_len*points, dtype=RENDERER_VERTEX_DTYPE)
    indices = np.empty((circles_len*(points-2), 3), dtype=np.uint32)

    for cind, ((x, y), rd, color) in enumerate(circles):
        assert rd > 0, "Why?"

        arr_cind = cind*points
        r, g, b = color

        angle = 0
        dt_angle = (np.pi*2)/points
        for point in range(points):
            verticies[arr_cind+point] = (
                (x+np.cos(angle)*rd, y+np.sin(angle)*rd), (0, 0), (r, g, b), PADDING
            )
            angle += dt_angle

        indx_cind = cind*(points-2)
        for ind in range(1, points-1):
            indices[indx_cind+ind-1] = [arr_cind, arr_cind+ind, arr_cind+ind+1]

    return DynamicMeshCPU(verticies.flatten(), indices.flatten(), RENDERER_VERTEX_DTYPE)

class DrawCall:
    """
    A single draw call is a combination of geometry and texture. 
    Draw calls can merge if their texture is the same
    """
    def __init__(self, mesh: DynamicMeshCPU, texture: gl.Texture):
        self.mesh = mesh
        self.texture = texture

    def can_merge(self, other: "DrawCall") -> bool:
        return self.texture == other.texture

    def merge(self, other: "DrawCall"):
        assert self.texture == other.texture
        self.mesh.add_mesh(other.mesh) 

    def __repr__(self) -> str:
        # V stands for verticies, T stands for texture
        return f"<DrawCall V:{self.mesh.vertex_elements()}, T:{self.texture.width}x{self.texture.height}>"

class DrawCallBatch:
    "Draw call container and merger"
    def __init__(self, verticies: int, indicies: int):
        self.reserved_mesh = ReservedMeshCPU(verticies, indicies, RENDERER_VERTEX_DTYPE)
        self.texture = None

    def can_merge(self, draw_call: DrawCall):
        # Only compatible if it can both fit its geometry and have the same texture
        # OR, if the texture is simply not set
        return (
            self.reserved_mesh.can_fit_mesh(draw_call.mesh) 
            and (self.texture is None or self.texture == draw_call.texture)
        )
    
    def merge_draw_call(self, draw_call: DrawCall):
        assert self.can_merge(draw_call), "The draw call exceeds the draw call batch limits"

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
        self.draw_commands: dict[int, list[DrawCall]] = {}
        """
        This map maps Z coordinates to lists of draw calls. Before rendering, the drawcalls in the list
        should also get sorted by their texture
        """

        self.current_z: int = 0
        """
        The current z coordinate of this renderer, used in most 2D operations.
        This is a public attribute, so do whatever you want with it
        """

        self.pipeline = Pipeline(
            self.ctx, 
            assets.load(gl.Program, "shaders/2d"),
            RENDERER_PIPELINE_PARAMS,
            RENDERER_VERTEX_ATTRIBUTES
        )

        self.vbo = self.ctx.buffer(reserve=vertex_elements*RENDERER_VERTEX_DTYPE.itemsize, dynamic=True)
        self.ibo = self.ctx.buffer(reserve=index_elements*4, dynamic=True)
        self.vao = self.ctx.vertex_array(
            self.pipeline.program, 
            [
                (self.vbo, RENDERER_VERTEX_GL_FORMAT, *self.pipeline.vertex_attributes)
            ],
            index_buffer=self.ibo
        )

    def increment_z(self):
        "Increment the current Z coordinate by 1. Allows for more explicit APIs"
        self.current_z += 1

    def decrement_z(self):
        "Decrement the current Z coordinate by 1. Allows for more explicit APIs"
        self.current_z -= 1

    def push_draw_call(self, draw_call: DrawCall, z: int = None):
        """
        Push an arbitrary draw call to the renderer. An additional Z coordinate can be provided 
        to specify the order of the draw call. If `None` - the current renderer's Z coordinate will
        be used instead.
        """

        self.draw_commands.setdefault(
            (self.current_z if z is None else z), 
            []
        ).append(draw_call)

    def _batch_draw_calls(self):
        """
        When we have collected all our draw calls, it's time to actually batch them. This will
        first sort all draw call groups based on their Z coordinate, and then based on their 
        textures inside the group.

        All groups will be cleared out after this operation
        """
        for _, draw_calls in sorted(self.draw_commands.items(), key=lambda item: item[0]):
            for draw_call in sorted(draw_calls, key=lambda dc: id(dc.texture)):
                if self.dc_ptr is None:
                    self.dc_ptr = 0
                
                batch = self.dc_batches[self.dc_ptr]

                if batch.can_merge(draw_call):
                    batch.merge_draw_call(draw_call)
                else:
                    self.dc_ptr += 1
                    assert self.dc_ptr < self.max_draw_calls, f"Reached a 2D draw call limit of {self.max_draw_calls}"
                    self.dc_batches[self.dc_ptr].merge_draw_call(draw_call)
            
            draw_calls.clear()

        # Just a design choice ig, but let's resent the current Z
        self.current_z = 0

    def reset_draw_call_batches(self):
        for batch in self.dc_batches[:self.dc_ptr+1]:
            batch.reset()

        self.dc_ptr = None

    def draw_rect_call(self, rect: tuple[int, ...], color: tuple[float, ...]) -> DrawCall:
        """
        Resetting means setting their internal pointers to zero and setting textures to `None`.
        
        Nothing is actually cleared, and all batches will get reused again
        """
        x, y, w, h = rect
        r, g, b = color
        rect_mesh = make_quad(
            ((x, y),     (0, 1), (r, g, b)),
            ((x+w, y),   (1, 1), (r, g, b)),
            ((x, y+h),   (0, 0), (r, g, b)),
            ((x+w, y+h), (1, 0), (r, g, b)),
        )
        return DrawCall(rect_mesh, self.white_texture.texture)

    def draw_rect(self, rect: tuple[int, ...], color: tuple[float, ...]):
        self.push_draw_call(self.draw_rect_call(rect, color))

    def draw_rects_call(self, entries: list[tuple[int, ...], tuple[float, ...]]):
        quads = make_quads([(
            ((x, y), (0, 1), color), 
            ((x+w, y), (1, 1), color),
            ((x, y+h), (0, 0), color),
            ((x+w, y+h), (1, 0), color),
        ) for (x, y, w, h), color in entries])
        return DrawCall(quads, self.white_texture.texture)
    
    def draw_rects(self, entries: list[tuple[int, ...], tuple[float, ...]]) -> DrawCall:
        "The same as `draw_rect`, but for A LOT of rectangles. Highly efficient"
        self.push_draw_call(self.draw_rects_call(entries))

    def draw_rect_lines_call(self, rect: tuple[int, ...], color: tuple[float, ...], thickness: float = 1):
        x, y, w, h = rect
        r, g, b = color
        t = thickness/2

        quads = make_quads([
            # TOP
            (
                ((x-t, y-t),     (0, 1), (r, g, b)),
                ((x+w+t, y-t),   (1, 1), (r, g, b)),
                ((x-t, y+t),   (0, 0), (r, g, b)),
                ((x+w+t, y+t), (1, 0), (r, g, b)),
            ),
            #LEFT
            (
                ((x-t, y-t),     (0, 1), (r, g, b)),
                ((x+t, y-t),   (1, 1), (r, g, b)),
                ((x-t, y+h+t),   (0, 0), (r, g, b)),
                ((x+t, y+h+t), (1, 0), (r, g, b)),
            ),
            # RIGHT
            (
                ((x+w-t, y-t),     (0, 1), (r, g, b)),
                ((x+w+t, y-t),   (1, 1), (r, g, b)),
                ((x+w-t, y+h+t),   (0, 0), (r, g, b)),
                ((x+w+t, y+h+t), (1, 0), (r, g, b)),
            ),
            # DOWN
            (
                ((x-t, y+h-t),     (0, 1), (r, g, b)),
                ((x+w+t, y+h-t),   (1, 1), (r, g, b)),
                ((x-t, y+h+t),   (0, 0), (r, g, b)),
                ((x+w+t, y+h+t), (1, 0), (r, g, b)),
            )
        ])

        return DrawCall(quads, self.white_texture.texture)
    
    def draw_rect_lines(self, rect: tuple[int, ...], color: tuple[float, ...], thickness: float = 1):
        self.push_draw_call(self.draw_rect_call(rect, color, thickness))

    def draw_texture_call(
            self, 
            texture: Texture,
            pos: tuple[int, ...], 
            size: tuple[int, ...] = None, 
            color: tuple[float, ...] = (1, 1, 1, 1),
        ):
        x, y = pos
        w, h = size if size is not None else texture.texture.size
        uv_x, uv_y, uv_w, uv_h = texture.region
        uv_w, uv_h = uv_x+uv_w, uv_y+uv_h

        return DrawCall(make_quad(
            ((x,    y),    (uv_x,     uv_y),         color),
            ((x+w, y),    (uv_w,      uv_y),         color),
            ((x,    y+h), (uv_x,     uv_h),     color),
            ((x+w, y+h), (uv_w, uv_h),     color)
        ), texture.texture)

    def draw_texture(
            self, 
            texture: Texture,
            pos: tuple[int, ...], 
            size: tuple[int, ...] = None, 
            color: tuple[float, ...] = (1, 1, 1, 1),
        ):
        """
        Draw a texture at a specified position with a specified size.

        The UV rect argument provided to this function takes absolute coordinates, instead of a normal rectangle
        `x, y, w, h`, you should instead provide `x, y, x+w, y+h`
        """
        self.push_draw_call(self.draw_texture_call(texture, pos, size, color))

    def draw_circle_call(self, pos: tuple[float, float], radius: float, color: tuple[float, ...], points: int = 20):
        circle_mesh = make_circle(pos, radius, color, points)
        return DrawCall(circle_mesh, self.white_texture.texture)

    def draw_circle(self, pos: tuple[float, float], radius: float, color: tuple[float, ...], points: int = 20):
        self.push_draw_call(self.draw_circle_call(pos, radius, color, points))

    def draw_circles_call(self, circles: tuple[tuple[tuple[int, int], int, tuple[float, float, float]]], points: int = 20):
        circles_mesh = make_circles(circles, points)
        return DrawCall(circles_mesh, self.white_texture.texture)

    def draw_circles(self, circles: tuple[tuple[tuple[int, int], int, tuple[float, float, float]]], points: int = 20):
        self.push_draw_call(self.draw_circles_call(circles, points))

    def draw_text_call(self, font: FontGPU, text: str, pos: tuple[int], color: tuple[float], size: float):
        x, y = pos
        x_offset = 0

        quads = []
        for char in text:
            texture = font.get_char_texture(char)
            uv_x, uv_y, uv_w, uv_h = texture.region
            uv_w, uv_h = uv_x+uv_w, uv_y+uv_h
            cw, ch = font.get_char_size(char)
            cw, ch = cw*size, ch*size
            offsetted_x = x+x_offset

            quads.append((
                ((offsetted_x,    y),    (uv_x, uv_y), color),
                ((offsetted_x+cw, y),    (uv_w, uv_y), color),
                ((offsetted_x,    y+ch), (uv_x, uv_h), color),
                ((offsetted_x+cw, y+ch), (uv_w, uv_h), color)
            ))

            x_offset += cw
        
        return DrawCall(make_quads(quads), font.get_texture())
    
    def draw_text(self, font: FontGPU, text: str, pos: tuple[int], color: tuple[float], size: float):
        self.push_draw_call(self.draw_text_call(font, text, pos, color, size))

    def draw(self, camera: Camera2D) -> int:
        "Render everything with the provided projection matrix, reset the draw batches and return the amount of draw calls"
        
        self._batch_draw_calls()

        if self.dc_ptr is None:
            # We have nothing to draw
            return

        draw_calls = 0
        self.pipeline["projection"] = camera.get_projection_matrix()
        self.pipeline.apply_params()
        for draw_batch in self.dc_batches[:self.dc_ptr+1]:
            verticies, indices = draw_batch.get_geometry()
            
            self.vbo.write(verticies)
            self.ibo.write(indices)

            vertex_elements = len(indices)

            draw_batch.texture.use()
            self.pipeline["texture_size"] = draw_batch.texture.size
            self.vao.render(vertices=vertex_elements)
            draw_calls += 1

        self.reset_draw_call_batches()

        return draw_calls

def issue_draw_calls(resources: Resources):
    draw_calls = resources[Renderer2D].draw(resources[Camera2D])

    resources[Telemetry].render2d_dcs = draw_calls

class Renderer2DPlugin(Plugin):
    def build(self, app):
        app.insert_resource(Renderer2D(
            app.get_resource(GraphicsContext),
            app.get_resource(AssetManager),
            MAX_VERTICIES,
            MAX_INDICES,
            MAX_DRAW_CALLS
        ))
        app.add_systems(Schedule.PostDraw, issue_draw_calls)