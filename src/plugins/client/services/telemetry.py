from plugin import Resources, Schedule, Plugin

from core.time import Clock
from core.assets import AssetManager
from core.telemetry import Telemetry

from core.graphics import FontGPU

from plugins.client.interfaces.gui import Label
from plugins.client.services.gui import GUIManager

class TelemetryState:
    def __init__(self, assets: AssetManager, gui: GUIManager):
        self.font = assets.load(FontGPU, "fonts/font.ttf")
        
        self.fps_label = Label(self.font, "FPS: 0", (0, 0), text_scale=0.3)
        self.fps_label.z = 100

        self.draw_calls_label = (Label(self.font, "Draw calls {{}}", (0, 1), text_scale=0.3)
            .attached_to(self.fps_label))

        gui.attach_elements(self.fps_label)

def update_counters(resources: Resources):
    telemetry = resources[Telemetry]
    state = resources[TelemetryState]

    fps = int(resources[Clock].get_fps())

    state.fps_label.set_text(
        f"FPS: {fps}"
    )
    state.draw_calls_label.set_text(
        f"Draw calls{{ 3D {telemetry.render3d_dcs}, 2D: {telemetry.render2d_dcs}, Sprite: {telemetry.sprite_dcs}}}"
    )

def create_telemetry(resources: Resources):
    resources.insert(TelemetryState(resources[AssetManager], resources[GUIManager]))

class TelemetryMenuPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Startup, create_telemetry)
        app.add_systems(Schedule.Update, update_counters)

