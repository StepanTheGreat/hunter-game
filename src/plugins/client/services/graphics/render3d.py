import moderngl as gl
import numpy as np

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
MODEL_VERTEX_DTYPE = np.dtype([
    ("position", "i2", 3),
    ("normal", "i1", 3),
    ("color", "u1", 3),
    ("uv", "u2", 2),
])
MODEL_VERTEX_GL_FORMAT = "3i2 3i1 3f1 2u2"


SKYBOX_PIPELINE_PARAMS = PipelineParams(
    cull_face=False,
    depth_test=False,
    alpha_blending=False,
    mode=gl.TRIANGLES
)

SKYBOX_VERTEX_ATTRIBUTES = ("position", "uv_ind")
SKYBOX_VERTEX_DTYPE = np.dtype([
    ("position", "f4", 3),
    ("uv_ind", "u4"),
])
SKYBOX_VERTEX_GL_FORMAT = "3f4 u4"

S = 0.75
"This a variable only for mesh construction purposes. It allows us to stretch our skybox height"

SKYBOX_MESH = DynamicMeshCPU(
    np.array([
        # Left face
        ((-1,  S, -1), 0),
        ((-1,  S,  1), 1),
        ((-1, -S, -1), 2),
        ((-1, -S,  1), 3),

        # Front face
        (( 1,  S, -1), 4),
        ((-1,  S, -1), 5),
        (( 1, -S, -1), 6),
        ((-1, -S, -1), 7),

        # Right face
        ((1,  S,  1), 8),
        ((1,  S, -1), 9),
        ((1, -S,  1), 10),
        ((1, -S, -1), 11),

        # Back face
        ((-1,  S,  1), 12),
        (( 1,  S,  1), 13),
        ((-1, -S,  1), 14),
        (( 1, -S,  1), 15),

    ], dtype=SKYBOX_VERTEX_DTYPE),
    np.array([
        1, 0, 2, 1, 2, 3, # Left face

        4, 5, 6, 6, 5, 7, # Front face

        8, 9, 10, 10, 9, 11, # Right face

        13, 12, 14, 13, 14, 15, # Back face
    ], dtype=np.uint32),
    vertex_dtype=SKYBOX_VERTEX_DTYPE
)

# To explain UV indexing, you might be confused why in most mesh construction we define explicit
# UV coordinates, but in this specific case we use "uv indexing". The reason why is to be able to 
# avoid constant skybox reconstruction when we simply change coordinates. Essentially, when rendering
# skyboxes - we have a 16 array of 2D UV vectors (which are integer pixel coordinates). We're going to
# index said vector using the defined in our geometry `uv_ind`.

class SkyBox:
    """
    A skybox is a box around our camera with a predefined texture that allows us to customize 
    the environment around (without it, everything is a static color).
    
    This skybox implementation uses texture atlases instead of cubemaps, and only 4 faces instead of
    6 (because our camera doesn't rotate around the Y axis)
    """
    def __init__(
        self, 
        left: Texture,
        front: Texture,
        right: Texture,
        back: Texture,
        color: tuple[float, float, float] = (1, 1, 1)
    ):
        assert all(
            texture.texture == left.texture for texture in (left, front, right, back)
        ), "Can't use different textures in a skybox"

        self.gl_texture: gl.Texture = left.texture
        self.color: tuple[float, float, float] = color

        self.uv_array = np.empty((16, 2), dtype=np.uint16)

        # We're filling the array with our UV coordinates
        for ind, texture in enumerate((left, front, right, back)):
            face_ind = ind*4
            x, y, w, h = texture.region
            w, h = x+w, y+h
            for coord_ind, uv_coord in enumerate(((x, y), (w, y), (x, h), (w, h))):
                self.uv_array[face_ind+coord_ind] = uv_coord
        
    def as_colored(texture: Texture, color: tuple[float, float, float]) -> "SkyBox":
        "Create colored skybox using a white-pixel texture"

        return SkyBox(
            texture,
            texture,
            texture,
            texture,
            color = color
        )

class ModelRenderer:
    """
    A renderer dedicated to rendering models. Compared to the dynamic 2D renderer, this one doesn't batch
    geometry at all. It simply stores all model rendering requests and then draws them.

    It's essentially a renderer for GPU geometry, while the 2D one is for CPU geometry. 
    """
    def __init__(self, gfx: GraphicsContext, assets: AssetManager):
        self.white_texture = gfx.get_white_texture()

        self.default_skybox: SkyBox = SkyBox.as_colored(
            self.white_texture,
            (0, 0, 0)
        )

        self.skybox = None
        
        self.models: list[tuple[Model, gl.Texture]] = []
        self.model_pipeline = Pipeline(
            gfx.get_context(),
            assets.load(gl.Program, "shaders/base"),
            MODEL_PIPELINE_PARAMS,
            MODEL_VERTEX_ATTRIBUTES
        )

        self.skybox_pipeline = Pipeline(
            gfx.get_context(),
            assets.load(gl.Program, "shaders/skybox"),
            SKYBOX_PIPELINE_PARAMS,
            SKYBOX_VERTEX_ATTRIBUTES
        )

        self.skybox_model = Model(
            gfx.get_context(),
            SKYBOX_MESH,
            self.skybox_pipeline,
            vertex_format=SKYBOX_VERTEX_GL_FORMAT
        )

    def get_pipeline(self) -> Pipeline:
        "Only models with the same pipeline can be accepted by this renderer"
        return self.model_pipeline
    
    def push_model(self, model: Model, texture: Optional[gl.Texture]):
        """
        Push a model to the rendering queue. The model should have the same pipeline as this renderer.
        If you leave the texture blank - a white 1x1 texture will be used instead. 
        """
        assert model.pipeline == self.model_pipeline, "Pipeline mismatch"

        if texture is None:
            texture = self.white_texture.texture
        self.models.append((model, texture))
    
    def clear(self):
        "Clear all models that are about to get rendered"
        self.models.clear()

    def _draw_skybox(self, cam: Camera3D):
        skybox: SkyBox = self.default_skybox if self.skybox is None else self.skybox

        self.skybox_pipeline["projection"] = cam.get_projection_matrix()
        self.skybox_pipeline["camera_rot"] = cam.get_camera_rotation().flatten()
        self.skybox_pipeline["skybox_color"] = skybox.color
        self.skybox_pipeline["skybox_uvs"] = skybox.uv_array
        self.skybox_pipeline["texture_size"] = skybox.gl_texture.size

        skybox.gl_texture.use()

        self.skybox_model.render()

    def _draw_models(self, lights: LightManager, camera: Camera3D) -> int:
        draw_calls = 0

        self.model_pipeline["projection"] = camera.get_projection_matrix()
        self.model_pipeline["camera_pos"] = camera.get_camera_position()
        self.model_pipeline["camera_rot"] = camera.get_camera_rotation().flatten()

        lights.apply_to_pipeline(self.model_pipeline)

        for model, texture in self.models:
            self.model_pipeline["texture_size"] = texture.size
            texture.use()
            model.render()
            draw_calls += 1

        return draw_calls
    
    def draw(self, lights: LightManager, camera: Camera3D) -> int:
        "Render all models and clear the list of models to draw"

        self._draw_skybox(camera)
        dcs = self._draw_models(lights, camera)

        self.models.clear()

        return dcs + 1 # +1 is for the skybox
    
    def set_skybox(self, skybox: Optional[SkyBox]):
        "Set this model's skybox when rendering. Setting it to `None` will make use of the default, black skybox"

        self.skybox = skybox

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