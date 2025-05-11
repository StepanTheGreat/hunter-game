from plugin import Plugin

from .session import SessionHandlersPlugin
from .character import CharacterHandlersPlugin
from .diamond import DiamondHandlersPlugin
from .entities import EntitiesHandlersPlugin

class ClientHandlersPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            SessionHandlersPlugin(),
            CharacterHandlersPlugin(),
            DiamondHandlersPlugin(),
            EntitiesHandlersPlugin()
        )