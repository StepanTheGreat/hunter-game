import moderngl as gl
import pygame as pg

from plugin import Plugin, Schedule, Resources
from core.graphics import *

SPRITE_MESH = MeshCPU(
    np.array([
        -0.5, 1, 0,     0, 0,
        0.5, 1, 0,     1, 0,
        -0.5, 0, 0,     0, 1,
        0.5, 0, 0,     1, 1
    ], dtype=np.float32),
    np.array([0, 1, 2, 1, 3, 2], dtype=np.uint32)
)

SPRITE_PIPELINE_PARAMS = PipelineParams(
    cull_face=False,
    depth_test=True
)

SPRITE_VERTEX_ATTRIBUTES = ("position", "uv")

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


class SpriteContainer:
    """
    A batching primitive for sprite rendering. 
    
    Every frame, sprites are supposed to push their positions, sizes and textures to this container.
    All the sprites will be automatically grouped based on their texture and rendred at the end of the frame.
    """
    def __init__(self, ctx: gl.Context, assets: AssetManager):
        self.map: dict[gl.Texture, list[int, np.ndarray, np.ndarray]] = {}
        model, pipeline = sprite_model(ctx, assets)
        self.model: Model = model
        self.pipeline: Pipeline = pipeline
        self.count = 0

    def push_sprite(self, texture: gl.Texture, pos: pg.Vector2, size: pg.Vector2):
        assert self.count < 255, "Reached a sprite limit"

        if texture in self.map:
            next_index, sprite_positions, sprite_sizes = self.map[texture]

            sprite_positions[next_index] = np.array([pos.x, -pos.y])
            sprite_sizes[next_index] = np.array([size.x, size.y])
            self.map[texture][0] = next_index+1
        else:

            sprite_positions = np.zeros((256, 2), dtype=np.float32)
            sprite_sizes = np.zeros((256, 2), dtype=np.float32)

            sprite_positions[0] = np.array([pos.x, -pos.y])
            sprite_sizes[0] = np.array([size.x, size.y])

            self.map[texture] = [
                1,
                sprite_positions, 
                sprite_sizes
            ]

        self.count += 1

    def get_sprite_uniform_arrays(self) -> list[tuple[gl.Texture, np.ndarray, np.ndarray]]:
        "Transform this sprite map into a list of tuples of `(texture, sprite_positions, sprite_sizes)`"
        return [(texture, sprite_positions, sprite_sizes) for texture, (_, sprite_positions, sprite_sizes) in self.map.items()]

    def get_pipeline(self) -> Pipeline:
        return self.pipeline
    
    def get_model(self) -> Model:
        return self.model

    def clear(self):
        self.count = 0
        self.map.clear()

def create_sprite_container(resources: Resources):
    gfx_ctx = resources[GraphicsContext]
    assets = resources[AssetManager]

    resources.insert(
        SpriteContainer(gfx_ctx.get_context(), assets)
    )

def clear_sprite_container(resources: Resources):
    resources[SpriteContainer].clear()

def render_sprite_container(resources: Resources):
    sprite_container = resources[SpriteContainer]
    
    camera = resources[Camera3D]

    pipeline = sprite_container.pipeline
    model = sprite_container.model

    pipeline["projection"] = camera.get_projection_matrix()
    pipeline["camera_pos"] = camera.get_camera_position()
    pipeline["camera_rot"] = camera.get_camera_rotation().flatten()
    
    for (texture, sprite_positions, sprite_sizes) in sprite_container.get_sprite_uniform_arrays():
        sprites_amount = sprite_positions.size//2
        pipeline["sprite_positions"] = sprite_positions
        pipeline["sprite_sizes"] = sprite_sizes
        texture.use()

        model.render(instances=sprites_amount)

class SpriteRendererPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Startup, create_sprite_container)
        app.add_systems(Schedule.PreRender, clear_sprite_container)
        app.add_systems(Schedule.PostRender, render_sprite_container)

