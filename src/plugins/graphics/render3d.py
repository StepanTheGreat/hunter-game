import moderngl as gl

from typing import Optional

from plugin import Plugin, Resources, Schedule

from core.telemetry import Telemetry
from core.assets import AssetManager
from core.graphics import *

MODEL_PIPELINE_PARAMS = PipelineParams(
    cull_face=True,
    depth_test=True,
    alpha_blending=False,
    mode=gl.TRIANGLES
)

MODEL_VERTEX_ATTRIBUTES = ("position", "color", "uv")

class ModelRenderer:
    """
    A renderer dedicated to rendering models. Compared to the dynamic 2D renderer, this one doesn't batch
    geometry at all. It simply stores all model rendering requests and then draws them.

    It's essentially a renderer for GPU geometry, while the 2D one is for CPU geometry. 
    """
    def __init__(self, gfx: GraphicsContext, assets: AssetManager):
        self.white_texture = gfx.get_white_texture()
        self.models: list[tuple[Model, gl.Texture]] = []
        self.pipeline = Pipeline(
            gfx.get_context(),
            assets.load(gl.Program, "shaders/base"),
            MODEL_PIPELINE_PARAMS,
            MODEL_VERTEX_ATTRIBUTES
        )

    def get_pipeline(self) -> Pipeline:
        "Only models with the same pipeline can be accepted by this renderer"
        return self.pipeline
    
    def push_model(self, model: Model, texture: Optional[gl.Texture]):
        """
        Push a model to the rendering queue. The model should have the same pipeline as this renderer.
        If you leave the texture blank - a white 1x1 texture will be used instead. 
        """
        assert model.pipeline == self.pipeline, "Pipeline mismatch"

        if texture is None:
            texture = self.white_texture

        self.models.append((model, texture))
    
    def clear(self):
        "Clear all models that are about to get rendered"
        self.models.clear()
    
    def draw(self, camera: Camera3D) -> int:
        "Render all models and clear the list of models to draw"
        self.pipeline["projection"] = camera.get_projection_matrix()
        self.pipeline["camera_pos"] = camera.get_camera_position()
        self.pipeline["camera_rot"] = camera.get_camera_rotation().flatten()

        draw_calls = 0
        for model, texture in self.models:
            texture.use()
            model.render()
            draw_calls += 1

        self.models.clear()

        return draw_calls

def draw_models(resources: Resources):
    draw_calls = resources[ModelRenderer].draw(resources[Camera3D])

    resources[Telemetry].render3d_dcs = draw_calls

class Renderer3DPlugin(Plugin):
    def build(self, app):
        app.insert_resource(ModelRenderer(
            app.get_resource(GraphicsContext),
            app.get_resource(AssetManager)
        ))
        app.add_systems(Schedule.PostDraw, draw_models)