import numpy as np

from plugin import Plugin, Schedule, Resources

from core.graphics import Pipeline

LIGHTS_LIMIT = 64

class Light:
    def __init__(self, pos: tuple[float, float], y: float, color: tuple[float, float, float], radius: float):
        self.pos = pos
        self.y = y
        self.color = color
        self.radius = radius

class LightManager:
    def __init__(self, ambient_color: tuple, max_lights: int):
        self.max_lights = max_lights
        self.lights: list[Light] = []

        self.ambient_color: tuple[float, float, float] = ambient_color
        "A public attribute which describes the color of the entire scene"

        self.light_positions = np.empty((self.max_lights, 3), dtype=np.float32)
        self.light_colors = np.empty((self.max_lights, 3), dtype=np.float32)
        self.light_radiuses = np.empty(self.max_lights, dtype=np.float32)

    def push_light(self, light: Light):
        assert len(self.lights) < self.max_lights
        self.lights.append(light)
    
    def remove_light(self, light: Light):
        try:
            self.lights.remove(light)
        except ValueError:
            pass

    def build_uniform_arrays(self):
        "This is updated internally"
        for ind, light in enumerate(self.lights):
            self.light_positions[ind] = (light.pos[0], light.y, -light.pos[1])
            self.light_colors[ind] = light.color
            self.light_radiuses[ind] = light.radius
    
    def get_light_positions(self) -> np.ndarray:
        return self.light_positions

    def get_light_colors(self) -> np.ndarray:
        return self.light_colors
    
    def get_lights_amount(self) -> int:
        return len(self.lights)
    
    def apply_to_pipeline(self, pipeline: Pipeline):
        pipeline["light_positions"] = self.light_positions
        pipeline["light_colors"] = self.light_colors
        pipeline["light_radiuses"] = self.light_radiuses

        pipeline["lights_amount"] = len(self.lights)
        pipeline["ambient_color"] = self.ambient_color

def update_lights(resources: Resources):
    resources[LightManager].build_uniform_arrays()

class LightPlugin(Plugin):
    def build(self, app):
        app.insert_resource(LightManager((0.05, 0.05, 0.1), LIGHTS_LIMIT))
        app.add_systems(Schedule.PostDraw, update_lights, priority=-1)
