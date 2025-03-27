from plugin import Resources, Schedule, Plugin

from core.pg import Clock
from core.assets import AssetManager
from core.telemetry import Telemetry

from core.graphics import FontGPU, Renderer2D

class TelemetryFont:
    def __init__(self, assets: AssetManager):
        self.font = assets.load(FontGPU, "fonts/font.ttf")

def show_fps(resources: Resources):
    renderer = resources[Renderer2D]
    telemetry = resources[Telemetry]

    font = resources[TelemetryFont].font
    font_height = font.get_height()

    fps = resources[Clock].get_fps()

    texts = (
        f"FPS: {int(fps)}",
        f"Draw calls{{ 3D {telemetry.render3d_dcs}, 2D: {telemetry.render2d_dcs}, Sprite: {telemetry.sprite_dcs}}}",
    )

    for line, text in enumerate(texts):
        renderer.draw_text(font, text, (0, line*(font_height/2)), (1, 1, 1), 0.5)

class TelemetryMenuPlugin(Plugin):
    def build(self, app):
        app.insert_resource(TelemetryFont(app.get_resource(AssetManager)))
        app.add_systems(Schedule.Render, show_fps)
