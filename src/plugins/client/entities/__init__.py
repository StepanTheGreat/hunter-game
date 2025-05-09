from plugin import Plugin

from .player import ClientPlayerPlugin
from .policeman import ClientPolicemanPlugin

class ClientEntitiesPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            ClientPlayerPlugin(),
            ClientPolicemanPlugin()
        )