"Everything related to rendering the game world"

from plugin import Plugin

from .telemetry import *
from .render2d import *
from .render3d import *
from .sprite import *

class GraphicsPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            Renderer3DPlugin(),
            SpriteRendererPlugin(),
            Renderer2DPlugin(),
            TelemetryMenuPlugin(),
        )