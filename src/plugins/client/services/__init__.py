from plugin import Plugin

from .playerstats import PlayerStatsPlugin
from .session import SessionPlugin
from .graphics import GraphicsPlugin
from .gui import GUIPlugin
from .perspective import PerspectivePlugin

class ClientServicesPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            GraphicsPlugin(),
            GUIPlugin(),
            PlayerStatsPlugin(),
            SessionPlugin(),
            PerspectivePlugin()
        )