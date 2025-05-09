from plugin import Plugin

from .playerstats import PlayerStatsPlugin
from .session import SessionPlugin

class ClientServicesPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            PlayerStatsPlugin(),
            SessionPlugin()
        )