import moderngl as gl
import numpy as np

from plugin import Plugin, Schedule, Resources
from app_config import CONFIG

from core.graphics import GraphicsContext, Pipeline, PipelineParams, Model, DynamicMeshCPU
from core.assets import AssetManager
from core.pg import Clock

from core.events import WindowResizeEvent

SCREEN_MESH = DynamicMeshCPU(
    np.array([
        -1.0,  1.0,     0.0, 1.0,
        1.0,  1.0,     1.0, 1.0,
        -1.0, -1.0,     0.0, 0.0,
        1.0, -1.0,     1.0, 0.0
    ], dtype=np.float32),
    np.array([0, 1, 2, 1, 2, 3], dtype=np.uint32)
)

POSTPROCESS_PARAMS = PipelineParams(
    cull_face=False,
    depth_test=False,
    alpha_blending=False
)

class PostProcessing:
    def __init__(self, gfx: GraphicsContext, assets: AssetManager):
        self.ctx = gfx.get_context()

        self.render_texture: gl.Texture = self.ctx.texture((CONFIG.width, CONFIG.height), 4)
        self.depth_texture: gl.Texture = self.ctx.depth_texture((CONFIG.width, CONFIG.height))

        self.framebuffer: gl.Framebuffer = self.ctx.framebuffer(
            color_attachments=[self.render_texture],
            depth_attachment=self.depth_texture
        )

        self.pipeline = Pipeline(
            self.ctx, 
            assets.load(gl.Program, "shaders/postprocessing"), 
            POSTPROCESS_PARAMS, 
            ("position", "uv")
        )
        self.model = Model(self.ctx, SCREEN_MESH, self.pipeline)

        self.time = 0
            
    def resize(self, new_width: int, new_height: int):
        "Resize the render texture"
        self.render_texture.release()
        self.framebuffer.release()
        self.depth_texture.release()

        self.render_texture = self.ctx.texture((new_width, new_height), 4)
        self.depth_texture = self.ctx.depth_texture((new_width, new_height))
    
        self.framebuffer = self.ctx.framebuffer(
            color_attachments=self.render_texture,
            depth_attachment=self.depth_texture
        )

    def apply_effects(self):
        # Attach our screen's primary framebuffer
        self.ctx.screen.use()
        # self.pipeline["time"] = self.time
        self.render_texture.use()
        self.model.render()

    def update_time(self, dt: float):
        self.time += dt

def on_screen_resize(resources: Resources, event: WindowResizeEvent):
    resources[PostProcessing].resize(event.new_width, event.new_height) 

def apply_effects(resources: Resources):
    post_processing = resources[PostProcessing]

    post_processing.update_time(resources[Clock].get_delta())
    post_processing.apply_effects()

def attach_render_framebuffer(resources: Resources):
    resources[PostProcessing].framebuffer.use()

class PostProcessingPlugin(Plugin):
    def build(self, app):
        app.insert_resource(PostProcessing(
            app.get_resource(GraphicsContext),
            app.get_resource(AssetManager)
        ))

        app.add_systems(Schedule.PostDraw, apply_effects, priority=1)
        app.add_systems(Schedule.PreDraw, attach_render_framebuffer, priority=-1)
        
        app.add_event_listener(WindowResizeEvent, on_screen_resize)