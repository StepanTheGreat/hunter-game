import numpy as np

from plugin import Plugin, Schedule, Resources

from core.graphics import Pipeline
from core.ecs import WorldECS, component

from plugins.components import RenderPosition

LIGHTS_LIMIT = 32

@component
class Light:
    def __init__(self, color: tuple[float, float, float], radius: float, luminosity: float):
        assert luminosity > 0
        assert radius > 0

        self.color = color
        self.radius = radius
        self.luminosity = luminosity

class LightManager:
    def __init__(self, ambient_color: tuple, max_lights: int):
        self.max_lights = max_lights

        self.ambient_color: tuple[float, float, float] = ambient_color
        "A public attribute which describes the color of the entire scene"

        self.light_positions = np.empty((self.max_lights, 3), dtype=np.int16)
        self.light_colors = np.empty((self.max_lights, 3), dtype=np.uint8)
        self.light_radiuses = np.empty(self.max_lights, dtype=np.uint16)
        self.light_luminosities = np.empty(self.max_lights, dtype=np.uint8)
        
        self.light_index = 0

    def push_light(self, light: Light, pos: RenderPosition):
        x, y = pos.get_position()
        height = pos.height

        self.light_positions[self.light_index] = (x, height, -y)
        self.light_colors[self.light_index] = light.color
        self.light_radiuses[self.light_index] = light.radius
        self.light_luminosities[self.light_index] = light.luminosity

        self.light_index += 1
    
    def get_light_positions(self) -> np.ndarray:
        return self.light_positions

    def get_light_colors(self) -> np.ndarray:
        return self.light_colors
    
    def get_lights_amount(self) -> int:
        return self.light_index
    
    def apply_to_pipeline(self, pipeline: Pipeline):
        pipeline["light_positions"] = self.light_positions
        pipeline["light_colors"] = self.light_colors
        pipeline["light_radiuses"] = self.light_radiuses
        pipeline["light_luminosities"] = self.light_luminosities

        pipeline["lights_amount"] = self.light_index
        pipeline["ambient_color"] = self.ambient_color

    def clear_lights(self):
        "Simply reset the internal "
        self.light_index = 0

def clear_lights(resources: Resources):
    resources[LightManager].clear_lights()

def push_lights(resources: Resources):
    lights = resources[LightManager]

    for ent, (light, pos) in resources[WorldECS].query_components(Light, RenderPosition)[:lights.max_lights]:
        lights.push_light(light, pos)

class LightPlugin(Plugin):
    def build(self, app):
        app.insert_resource(LightManager((0.05, 0.05, 0.1), LIGHTS_LIMIT))
        app.add_systems(Schedule.PreDraw, clear_lights, push_lights, priority=-1)
