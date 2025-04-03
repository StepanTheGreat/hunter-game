from plugin import Resources, Schedule, Plugin

from core.pg import Clock
from core.assets import AssetManager
from core.telemetry import Telemetry

from core.graphics import FontGPU

from plugins.gui import GUIManager, Label

class TelemetryState:
    def __init__(self, assets: AssetManager, gui: GUIManager):
        self.font = assets.load(FontGPU, "fonts/font.ttf")
        
        label = Label(self.font, "hello", (0, 0), (0, 0))
        label.set_position(0, 0)
        label2 = Label(self.font, "again?", (1, 0), (0, 0))
        label2.attach_to(label)

        label3 = Label(self.font, "This is cool!", (0, 1), (0, 0))
        label3.attach_to(label2)

        label4 = Label(self.font, "Indeed!", (1, 1), (0, 0))
        label4.attach_to(label3)

        gui.add_elements(label)

def update_counters(resources: Resources):
    telemetry = resources[Telemetry]
    state = resources[TelemetryState]

    fps = int(resources[Clock].get_fps())

    # state.fps_label.set_text(
    #     f"FPS: {fps}"
    # )
    # state.drawcalls_label.set_text(
    #     f"Draw calls{{ 3D {telemetry.render3d_dcs}, 2D: {telemetry.render2d_dcs}, Sprite: {telemetry.sprite_dcs}}}"
    # )

def create_telemetry(resources: Resources):
    resources.insert(TelemetryState(resources[AssetManager], resources[GUIManager]))

class TelemetryMenuPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Startup, create_telemetry)
        app.add_systems(Schedule.Update, update_counters)

