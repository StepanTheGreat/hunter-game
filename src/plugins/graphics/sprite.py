"Sprite rendering"

import moderngl as gl
import pygame as pg
import numpy as np

from plugin import Plugin, Schedule, Resources

from core.graphics import *
from core.telemetry import Telemetry
from core.assets import AssetManager
from core.ecs import WorldECS, component

from .lights import LightManager
from plugins.perspective import CurrentPerspectiveAttached
from plugins.components import RenderPosition

SPRITE_LIMIT = 64

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

@component
class Sprite:
    "A sprite component that allows an entity to be rendered as 2D billboards"
    def __init__(self, texture: Texture, size: pg.Vector2):
        self.texture: Texture = texture
        self.size: pg.Vector2 = size

class SpriteRenderer:
    "A separate pipeline for rendering 2D sprites in 3D"
    class SpriteGroup:
        def __init__(self, size: int):
            self.amount = 0
            self.sprite_positions = np.zeros((size, 3), dtype=np.int16)
            self.sprite_sizes = np.zeros((size, 2), dtype=np.uint8)
            self.sprite_uv_rects = np.zeros((size, 4), dtype=np.uint16)

        def add(self, sprite: Sprite, pos: tuple[float, float], y: float):
            size = sprite.size
            uvx, uvy, uvw, uvh = sprite.texture.region
            #uv_rect is a tuple of 4 absolute texture coordinates

            self.sprite_positions[self.amount] = np.array([pos[0], y, -pos[1]])
            self.sprite_sizes[self.amount] = np.array([size.x, size.y])
            self.sprite_uv_rects[self.amount] = (uvx, uvy, uvx+uvw, uvy+uvh)
            self.amount += 1

        def get_uniforms(self) -> tuple[np.ndarray]:
            return (
                self.sprite_positions,
                self.sprite_sizes,
                self.sprite_uv_rects
            )
        
        def get_amount(self) -> int:
            return self.amount
        
        def reset(self):
            self.amount = 0
        
    """
    A batching primitive for sprite rendering. 
    
    Every frame, sprites are supposed to push their positions, sizes, uv_rects and textures to this container.
    All the sprites will automatically get grouped based on their texture and rendred at the end of the frame.
    """
    def __init__(self, sprite_limit: int, gfx: GraphicsContext, assets: AssetManager):
        self.ctx = gfx.get_context()
        self.sprite_limit = sprite_limit

        self.groups: dict[gl.Texture, SpriteRenderer.SpriteGroup] = {}

        model, pipeline = sprite_model(self.ctx, assets)
        self.model: Model = model
        self.pipeline: Pipeline = pipeline
        self.can_draw: bool = True
        
    def push_sprite(self, sprite: Sprite, pos: tuple[float, float], y: float):  
        texture = sprite.texture
        gl_texture = texture.texture

        if gl_texture not in self.groups:
            self.groups[gl_texture] = SpriteRenderer.SpriteGroup(self.sprite_limit)

        self.groups[gl_texture].add(sprite, pos, y)

    def get_sprite_uniform_arrays(self) -> list[tuple[int, gl.Texture, np.ndarray, np.ndarray, np.ndarray]]:
        """Transform this sprite map into a list of tuples of:
        `(amount, texture, sprite_positions, sprite_sizes, sprite_uv_rects)`
        """
        return [(sprite_group.get_amount(), texture, *sprite_group.get_uniforms()) for texture, sprite_group in self.groups.items()]

    def clear_sprite_groups(self):
        for group in self.groups.values():
            group.reset()

    def draw(self, lights: LightManager, camera: Camera3D) -> int:     
        # self.clear_sprite_groups(); return 0

        self.pipeline["projection"] = camera.get_projection_matrix()
        self.pipeline["camera_pos"] = camera.get_camera_position()
        self.pipeline["camera_rot"] = camera.get_camera_rotation().flatten()

        lights.apply_to_pipeline(self.pipeline)

        draw_calls = 0
        
        for (amount, texture, sprite_positions, sprite_sizes, sprite_uv_rects) in self.get_sprite_uniform_arrays():
            self.pipeline["sprite_positions"] = sprite_positions
            self.pipeline["sprite_sizes"] = sprite_sizes
            self.pipeline["sprite_uv_rects"] = sprite_uv_rects
            
            self.pipeline["texture_size"] = texture.size
            texture.use()
            self.model.render(instances=amount)
            draw_calls += 1

        self.clear_sprite_groups()

        return draw_calls

def draw_sprites(resources: Resources):
    """
    Collect all entities with Position and Sprite components, add them for rendering and then... render?
    """
    lights = resources[LightManager]
    renderer = resources[SpriteRenderer]
    current_perspective_entity = resources[CurrentPerspectiveAttached].attached_entity

    for ent, (position, sprite) in resources[WorldECS].query_components(RenderPosition, Sprite)[:renderer.sprite_limit]:
        if ent != current_perspective_entity:
            # If the entity is the current camera entity - we should ignore its sprite
            renderer.push_sprite(sprite, position.get_position(), position.height)

    draw_calls = renderer.draw(lights, resources[Camera3D])

    resources[Telemetry].sprite_dcs = draw_calls

class SpriteRendererPlugin(Plugin):
    def build(self, app):
        app.insert_resource(SpriteRenderer(
            SPRITE_LIMIT,
            app.get_resource(GraphicsContext),
            app.get_resource(AssetManager)
        ))
        app.add_systems(Schedule.PostDraw, draw_sprites)
