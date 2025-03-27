"Everything related to rendering the game world"

from plugin import Plugin

from .minimap import *
from .map import *
from .telemetry import *

class RenderPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            MinimapPlugin(),
            TelemetryMenuPlugin(),
            MapRendererPlugin()
        )