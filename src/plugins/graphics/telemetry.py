from plugin import Resources, Schedule, Plugin

from core.pg import Clock
from core.assets import AssetManager
from core.telemetry import Telemetry

from core.graphics import FontGPU

from plugins.gui import GUIManager, Label, Button

class TelemetryState:
    def __init__(self, assets: AssetManager, gui: GUIManager):
        self.font = assets.load(FontGPU, "fonts/font.ttf")
        
        self.fps_label = Label("fps_counter", self.font, "0", (0, 0), scale=0.5)
        self.drawcalls_label = Label("drawcalls", self.font, "Draw calls {{}}", (0, 0.05), scale=0.5)
        self.button = Button("btn", self.font, "Click me", (0.5, 0.5), pivot=(0.5, 0.5), text_scale=0.5)

        gui.add_elements(
            (10, self.fps_label),
            (10, self.drawcalls_label),
            (1, self.button)
        )

def update_counters(resources: Resources):
    telemetry = resources[Telemetry]
    state = resources[TelemetryState]

    fps = int(resources[Clock].get_fps())

    state.fps_label.set_text(
        f"FPS: {fps}"
    )
    state.drawcalls_label.set_text(
        f"Draw calls{{ 3D {telemetry.render3d_dcs}, 2D: {telemetry.render2d_dcs}, Sprite: {telemetry.sprite_dcs}}}"
    )

def create_telemetry(resources: Resources):
    resources.insert(TelemetryState(resources[AssetManager], resources[GUIManager]))

class TelemetryMenuPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Startup, create_telemetry)
        app.add_systems(Schedule.Update, update_counters)

