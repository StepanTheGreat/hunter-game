from plugin import Plugin

from .base import BaseHandlersPlugin
from .characters import CharactersHandlersPlugin
from .diamond import DiamondHandlersPlugin
from .projectile import ProjectileHandlersPlugin
from .session import SessionHandlersPlugin

class ServerHandlersPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            BaseHandlersPlugin(),
            CharactersHandlersPlugin(),
            DiamondHandlersPlugin(),
            ProjectileHandlersPlugin(),
            SessionHandlersPlugin()
        )