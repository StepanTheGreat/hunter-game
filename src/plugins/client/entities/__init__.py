from plugin import Plugin

from .player import ClientPlayerPlugin
from .policeman import ClientPolicemanPlugin
from .diamond import ClientDiamondPlugin

class ClientEntitiesPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            ClientPlayerPlugin(),
            ClientPolicemanPlugin(),
            ClientDiamondPlugin()
        )