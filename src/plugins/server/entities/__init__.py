from plugin import Plugin

from .projectile import ServerProjectilePlugin
from .diamond import ServerDiamondPlugin

class ServerEntitiesPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            ServerProjectilePlugin(),
            ServerDiamondPlugin()
        )