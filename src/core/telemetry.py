from plugin import Plugin

class Telemetry:
    "GPU information for debugging and optimisations. All attributes are public, this is just a global state"
    def __init__(self):
        self.sprite_dcs: int = 0
        self.render3d_dcs: int = 0
        self.render2d_dcs: int = 0

class TelemetryPlugin(Plugin):
    def build(self, app):
        app.insert_resource(Telemetry())
