from plugin import Plugin

from .player import ClientPlayerPlugin
from .characters import ClientCharactersPlugin
from .diamond import ClientDiamondPlugin

class ClientEntitiesPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            ClientPlayerPlugin(),
            ClientCharactersPlugin(),
            ClientDiamondPlugin()
        )