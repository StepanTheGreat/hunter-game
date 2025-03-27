from plugin import Resources, Schedule, Plugin

from core.pg import Clock
from core.assets import AssetManager
from core.entity import EntityWorld

from core.graphics import FontGPU, Renderer2D

from ..entities.player import Player
from ..entities.sprite import Sprite

from ..map import WorldMap, TILE_SIZE

MINIMAP_SCALE = 0.5

class FPSCounter:
    def __init__(self, assets: AssetManager):
        self.font = assets.load(FontGPU, "fonts/font.ttf")

def show_fps(resources: Resources):
    counter = resources[FPSCounter]
    renderer = resources[Renderer2D]
    clock = resources[Clock]

    fps_text = str(int(clock.get_fps()))
    renderer.draw_text(counter.font, fps_text, (0, -4), (1, 1, 1), 1)

class FPSCounterPlugin(Plugin):
    def build(self, app):
        app.insert_resource(
            FPSCounter(app.get_resource(AssetManager))
        )
        app.add_systems(Schedule.Render, show_fps)
