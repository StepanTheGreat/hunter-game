import moderngl as gl

from typing import Optional

from plugin import Plugin, Resources, Schedule

from core.telemetry import Telemetry
from core.assets import AssetManager
from core.graphics import *

from .lights import LightManager

MODEL_PIPELINE_PARAMS = PipelineParams(
    cull_face=True,
    depth_test=True,
    alpha_blending=False,
    mode=gl.TRIANGLES
)

MODEL_VERTEX_ATTRIBUTES = ("position", "normal", "color", "uv")

def make_quads_3d(quads: list[tuple[tuple[float, ...], tuple[float, ...], tuple[float, 3], tuple[float, float]]]) -> DynamicMeshCPU:
    "The same as `make_quads` from render2d, but for 3D quads"

    quads_len = len(quads)

    verticies = np.zeros((quads_len, 3+3+3+2), dtype=np.float32)
    indices = np.zeros((quads_len, 6), dtype=np.uint32)

    lind = 0
    for ind, quad in enumerate(quads):
        p1, p2, p3, p4 = quad

        verticies[ind] = [
            *p1[0],   *p1[1],  *p1[2], *p1[3],
            *p2[0],   *p2[1],  *p2[2], *p2[3],
            *p3[0],   *p3[1],  *p3[2], *p3[3],
            *p4[0],   *p4[1],  *p4[2], *p4[3],
        ]
        indices[ind] = [lind, lind+1, lind+2, lind+1, lind+2, lind+3]
        lind += 4
    
    return DynamicMeshCPU(verticies.ravel(), indices.ravel())

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
    
    def draw(self, lights: LightManager, camera: Camera3D) -> int:
        "Render all models and clear the list of models to draw"
        self.pipeline["projection"] = camera.get_projection_matrix()
        self.pipeline["camera_pos"] = camera.get_camera_position()
        self.pipeline["camera_rot"] = camera.get_camera_rotation().flatten()

        lights.apply_to_pipeline(self.pipeline)

        draw_calls = 0
        for model, texture in self.models:
            texture.use()
            model.render()
            draw_calls += 1

        self.models.clear()

        return draw_calls

def draw_models(resources: Resources):
    lights = resources[LightManager]
    draw_calls = resources[ModelRenderer].draw(lights, resources[Camera3D])

    resources[Telemetry].render3d_dcs = draw_calls

class Renderer3DPlugin(Plugin):
    def build(self, app):
        app.insert_resource(ModelRenderer(
            app.get_resource(GraphicsContext),
            app.get_resource(AssetManager)
        ))
        app.add_systems(Schedule.PostDraw, draw_models)