from plugin import Plugin

from .characters import ClientCharactersPlugin
from .diamond import ClientDiamondPlugin

class ClientEntitiesPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            ClientCharactersPlugin(),
            ClientDiamondPlugin()
        )