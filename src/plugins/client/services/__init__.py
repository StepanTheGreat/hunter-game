from plugin import Plugin

from .playerstats import PlayerStatsPlugin
from .session import SessionPlugin
from .graphics import GraphicsPlugin
from .gui import GUIPlugin
from .perspective import PerspectivePlugin
from .telemetry import TelemetryMenuPlugin

from .minimap import MinimapPlugin
from .maprender import MapRendererPlugin

class ClientServicesPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            GraphicsPlugin(),

            MapRendererPlugin(),
            MinimapPlugin(),

            GUIPlugin(),
            PlayerStatsPlugin(),
            SessionPlugin(),
            PerspectivePlugin(),
            TelemetryMenuPlugin()
        )