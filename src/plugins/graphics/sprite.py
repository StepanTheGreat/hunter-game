"Sprite rendering"

import moderngl as gl
import pygame as pg
import numpy as np

from plugin import Plugin, Schedule, Resources

from core.graphics import *
from core.telemetry import Telemetry
from core.assets import AssetManager

from .render3d import LightManager

SPRITE_MESH = DynamicMeshCPU(
    # To explain this confusing matrix of 4 numbers (the last one)
    # It is essentially a UV coordinate matrix that goes like this: x, y, x+w, y+h
    #
    # We're doing this because when drawing textures with specific texture coordinates - each vertex should
    # have its own specific x,y UV coordinate. But to do this we will have to perform `if` checks that are quite
    # expensive on the GPU or reconstruct the geometry entirely every time, thus not allowing us to 
    # benefit from instancing. Well, using this simple matrix mask, we can get our UV coordinates using extremely 
    # simple math:
    # (uv.x*mat.x+uv.w*mat.w, uv.y*mat.y+uv.h+mat.h) 
    # That's it!
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

class Sprite:
    def __init__(self, texture: gl.Texture, pos: pg.Vector2, size: pg.Vector2, uv_rect: tuple):
        self.texture = texture
        self.position = pos
        self.size = size
        self.uv_rect = uv_rect
class Sprite:
    def __init__(self, texture: gl.Texture, pos: pg.Vector2, size: pg.Vector2, uv_rect: tuple):
        self.texture = texture
        self.position = pos
        self.size = size
        self.uv_rect = uv_rect

class SpriteRenderer:
    "A separate pipeline for rendering 2D sprites in 3D"
    class SpriteGroup:
        def __init__(self, size: int):
            self.amount = 0
            self.sprite_positions = np.zeros((size, 2), dtype=np.float32)
            self.sprite_sizes = np.zeros((size, 2), dtype=np.float32)
            self.sprite_uv_rects = np.zeros((size, 4), dtype=np.float32)

        def add(self, sprite: Sprite):
        def add(self, sprite: Sprite):
            "uv_rect is a tuple of 4 absolute texture coordinates"

            pos = sprite.position
            size = sprite.size
            uv_rect = sprite.uv_rect

            pos = sprite.position
            size = sprite.size
            uv_rect = sprite.uv_rect

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
        
        self.sprites: list[Sprite] = []
        self.sprites: list[Sprite] = []

    def push_sprite(self, sprite: Sprite):        
        self.sprites.append(sprite)

    def remove_sprite(self, sprite: Sprite):
        "Try remove the sprite if it's present"
        try:
            self.sprites.remove(sprite)
        except ValueError:
            pass
    def push_sprite(self, sprite: Sprite):        
        self.sprites.append(sprite)

    def remove_sprite(self, sprite: Sprite):
        "Try remove the sprite if it's present"
        try:
            self.sprites.remove(sprite)
        except ValueError:
            pass

    def get_sprite_uniform_arrays(self) -> list[tuple[int, gl.Texture, np.ndarray, np.ndarray, np.ndarray]]:
        """Transform this sprite map into a list of tuples of:
        `(amount, texture, sprite_positions, sprite_sizes, sprite_uv_rects)`
        """
        return [(sprite_group.get_amount(), texture, *sprite_group.get_uniforms()) for texture, sprite_group in self.groups.items()]
    
    def build_sprite_groups(self):
        for sprite in self.sprites:
            texture = sprite.texture

            if texture not in self.groups:
                self.groups[texture] = SpriteRenderer.SpriteGroup(256)

            group = self.groups[texture]
            group.add(sprite)

    def clear_sprite_groups(self):
    def build_sprite_groups(self):
        for sprite in self.sprites:
            texture = sprite.texture

            if texture not in self.groups:
                self.groups[texture] = SpriteRenderer.SpriteGroup(256)

            group = self.groups[texture]
            group.add(sprite)

    def clear_sprite_groups(self):
        self.groups.clear()

    def draw(self, lights: LightManager, camera: Camera3D) -> int:
        self.build_sprite_groups()
        
        self.pipeline["projection"] = camera.get_projection_matrix()
        self.pipeline["camera_pos"] = camera.get_camera_position()
        self.pipeline["camera_rot"] = camera.get_camera_rotation().flatten()

        lights.apply_to_pipeline(self.pipeline)

        draw_calls = 0
        
        for (amount, texture, sprite_positions, sprite_sizes, sprite_uv_rects) in self.get_sprite_uniform_arrays():
            self.pipeline["sprite_positions"] = sprite_positions
            self.pipeline["sprite_sizes"] = sprite_sizes
            self.pipeline["sprite_uv_rects"] = sprite_uv_rects

            texture.use()
            self.model.render(instances=amount)
            draw_calls += 1

        self.clear_sprite_groups()
        self.clear_sprite_groups()

        return draw_calls

def draw_sprites(resources: Resources):
    lights = resources[LightManager]
    draw_calls = resources[SpriteRenderer].draw(lights, resources[Camera3D])

    resources[Telemetry].sprite_dcs = draw_calls

class SpriteRendererPlugin(Plugin):
    def build(self, app):
        app.insert_resource(SpriteRenderer(
            app.get_resource(GraphicsContext),
            app.get_resource(AssetManager)
        ))
        app.add_systems(Schedule.PostDraw, draw_sprites)

