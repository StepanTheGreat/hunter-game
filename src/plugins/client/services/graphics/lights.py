import numpy as np

from plugin import Plugin, Schedule, Resources

from core.graphics import Pipeline
from core.ecs import WorldECS

from plugins.client.components import RenderPosition, Light

LIGHTS_LIMIT = 32
DEFAULT_AMBIENT_LIGHT = (1, 1, 1)

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

        self.lights_enabled: bool = True
        """
        A public attribute that signals if lights are enabled. When lights are disabled - the lights passed
        to this manager will not get used in rendering. This can be useful when the overall brightness
        of your scene changes and lights are redundant. 
        """

    def set_ambient_color(self, to: tuple[float, float, float]):
        self.ambient_color = to

    def push_light(self, light: Light, pos: RenderPosition):
        if not self.lights_enabled:
            return

        x, y = pos.get_position()

        self.light_positions[self.light_index] = (x, light.y, -y)
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

    # If lights are disabled - there's no reason for us to perform any queries or push anything
    if not lights.lights_enabled:
        return

    for ent, (light, pos) in resources[WorldECS].query_components(Light, RenderPosition)[:lights.max_lights]:
        lights.push_light(light, pos)

class LightPlugin(Plugin):
    def build(self, app):
        app.insert_resource(LightManager(DEFAULT_AMBIENT_LIGHT, LIGHTS_LIMIT))
        app.add_systems(Schedule.PreDraw, clear_lights, push_lights, priority=-1)
