"Sprite rendering"

import moderngl as gl
import pygame as pg
import numpy as np

from plugin import Plugin, Schedule, Resources

from .objects import *
from .camera import Camera3D
from .ctx import GraphicsContext

from core.telemetry import Telemetry
from core.assets import AssetManager

SPRITE_MESH = DumbMeshCPU(
    np.array([
        -0.5, 1, 0,     1, 1, 0, 0,
         0.5, 1, 0,     0, 1, 1, 0,
        -0.5, 0, 0,     1, 0, 0, 1,
         0.5, 0, 0,     0, 0, 1, 1,
    ], dtype=np.float32),
    np.array([0, 1, 2, 1, 3, 2], dtype=np.uint32)
)

SPRITE_PIPELINE_PARAMS = PipelineParams(
    cull_face=False,
    depth_test=True,
    alpha_blending=False
)

SPRITE_VERTEX_ATTRIBUTES = ("position", "uv_mat")

def sprite_model(ctx: gl.Context, assets: AssetManager) -> tuple[Model, Pipeline]:
    pipeline = Pipeline(
        ctx,
        assets.load(gl.Program, "shaders/sprite"),
        SPRITE_PIPELINE_PARAMS,
        SPRITE_VERTEX_ATTRIBUTES
    )
    model = Model (
        ctx,
        SPRITE_MESH,
        pipeline
    )
    return model, pipeline


class SpriteRenderer:
    "A separate pipeline for rendering 2D sprites in 3D"
    class SpriteGroup:
        def __init__(self, size: int):
            self.amount = 0
            self.sprite_positions = np.zeros((size, 2), dtype=np.float32)
            self.sprite_sizes = np.zeros((size, 2), dtype=np.float32)
            self.sprite_uv_rects = np.zeros((size, 4), dtype=np.float32)

        def add(self, pos: pg.Vector2, size: pg.Vector2, uv_rect: tuple[float]):
            "uv_rect is a tuple of 4 absolute texture coordinates"

            self.sprite_positions[self.amount] = np.array([pos.x, -pos.y])
            self.sprite_sizes[self.amount] = np.array([size.x, size.y])
            self.sprite_uv_rects[self.amount] = np.array(uv_rect)
            self.amount += 1

        def get_uniforms(self) -> tuple[np.ndarray]:
            return (
                self.sprite_positions,
                self.sprite_sizes,
                self.sprite_uv_rects
            )
        
        def get_amount(self) -> int:
            return self.amount
        
    """
    A batching primitive for sprite rendering. 
    
    Every frame, sprites are supposed to push their positions, sizes, uv_rects and textures to this container.
    All the sprites will automatically get grouped based on their texture and rendred at the end of the frame.
    """
    def __init__(self, gfx: GraphicsContext, assets: AssetManager):
        self.ctx = gfx.get_context()

        self.groups: dict[gl.Texture, SpriteRenderer.SpriteGroup] = {}

        model, pipeline = sprite_model(self.ctx, assets)
        self.model: Model = model
        self.pipeline: Pipeline = pipeline
        
        self.count = 0

    def push_sprite(self, texture: gl.Texture, pos: pg.Vector2, size: pg.Vector2, uv_rect: tuple[float]):
        assert self.count < 255, "Reached a sprite limit"

        if texture in self.groups:
            group = self.groups[texture]
            group.add(pos, size, uv_rect)
        else:

            group = SpriteRenderer.SpriteGroup(256)
            group.add(pos, size, uv_rect)
            self.groups[texture] = group

        self.count += 1

    def get_sprite_uniform_arrays(self) -> list[tuple[int, gl.Texture, np.ndarray, np.ndarray, np.ndarray]]:
        """Transform this sprite map into a list of tuples of:
        `(amount, texture, sprite_positions, sprite_sizes, sprite_uv_rects)`
        """
        return [(sprite_group.get_amount(), texture, *sprite_group.get_uniforms()) for texture, sprite_group in self.groups.items()]
    
    def clear(self):
        self.count = 0
        self.groups.clear()

    def draw(self, camera: Camera3D) -> int:
        self.pipeline["projection"] = camera.get_projection_matrix()
        self.pipeline["camera_pos"] = camera.get_camera_position()
        self.pipeline["camera_rot"] = camera.get_camera_rotation().flatten()

        draw_calls = 0
        
        for (amount, texture, sprite_positions, sprite_sizes, sprite_uv_rects) in self.get_sprite_uniform_arrays():
            self.pipeline["sprite_positions"] = sprite_positions
            self.pipeline["sprite_sizes"] = sprite_sizes
            self.pipeline["sprite_uv_rects"] = sprite_uv_rects

            texture.use()
            self.model.render(instances=amount)
            draw_calls += 1

        self.clear()

        return draw_calls

def draw_sprites(resources: Resources):
    draw_calls = resources[SpriteRenderer].draw(resources[Camera3D])

    resources[Telemetry].sprite_dcs = draw_calls

class SpriteRendererPlugin(Plugin):
    def build(self, app):
        app.insert_resource(SpriteRenderer(
            app.get_resource(GraphicsContext),
            app.get_resource(AssetManager)
        ))
        app.add_systems(Schedule.PostRender, draw_sprites)

