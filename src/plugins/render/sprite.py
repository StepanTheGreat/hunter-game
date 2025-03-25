import moderngl as gl
import pygame as pg

from plugin import Plugin, Schedule, Resources
from core.graphics import *

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


class SpriteContainer:

    class SpriteGroup:
        def __init__(self, size: int):
            self.next_index = 0
            self.sprite_positions = np.zeros((size, 2), dtype=np.float32)
            self.sprite_sizes = np.zeros((size, 2), dtype=np.float32)
            self.sprite_uv_rects = np.zeros((size, 4), dtype=np.float32)

        def add(self, pos: pg.Vector2, size: pg.Vector2, uv_rect: tuple[float]):
            "uv_rect is a tuple of 4 absolute texture coordinates"

            self.sprite_positions[self.next_index] = np.array([pos.x, -pos.y])
            self.sprite_sizes[self.next_index] = np.array([size.x, size.y])
            self.sprite_uv_rects[self.next_index] = np.array(uv_rect)
            self.next_index += 1

        def get_uniforms(self) -> tuple[np.ndarray]:
            return (
                self.sprite_positions,
                self.sprite_sizes,
                self.sprite_uv_rects
            )
        
    """
    A batching primitive for sprite rendering. 
    
    Every frame, sprites are supposed to push their positions, sizes, uv_rects and textures to this container.
    All the sprites will automatically get grouped based on their texture and rendred at the end of the frame.
    """
    def __init__(self, ctx: gl.Context, assets: AssetManager):
        self.map: dict[gl.Texture, SpriteContainer.SpriteGroup] = {}
        "This map maps textures to a sprite entry of `(next_index, sprite_positions, sprite_sizes, sprite_uv_rects)`"

        model, pipeline = sprite_model(ctx, assets)
        self.model: Model = model
        self.pipeline: Pipeline = pipeline
        
        self.count = 0

    def push_sprite(self, texture: gl.Texture, pos: pg.Vector2, size: pg.Vector2, uv_rect: tuple[float]):
        assert self.count < 255, "Reached a sprite limit"

        if texture in self.map:
            group = self.map[texture]
            group.add(pos, size, uv_rect)
        else:

            group = SpriteContainer.SpriteGroup(256)
            group.add(pos, size, uv_rect)
            self.map[texture] = group

        self.count += 1

    def get_sprite_uniform_arrays(self) -> list[tuple[gl.Texture, np.ndarray, np.ndarray]]:
        "Transform this sprite map into a list of tuples of `(texture, sprite_positions, sprite_sizes)`"
        return [(texture, *sprite_group.get_uniforms()) for texture, sprite_group in self.map.items()]

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
    
    for (texture, sprite_positions, sprite_sizes, sprite_uv_rects) in sprite_container.get_sprite_uniform_arrays():
        sprites_amount = sprite_positions.size//2
        pipeline["sprite_positions"] = sprite_positions
        pipeline["sprite_sizes"] = sprite_sizes
        pipeline["sprite_uv_rects"] = sprite_uv_rects
        texture.use()

        model.render(instances=sprites_amount)

class SpriteRendererPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Startup, create_sprite_container)
        app.add_systems(Schedule.PreRender, clear_sprite_container)
        app.add_systems(Schedule.PostRender, render_sprite_container)

