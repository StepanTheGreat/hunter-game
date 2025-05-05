from plugin import Plugin

from .projectile import ServerProjectilePlugin

class ServerEntitiesPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            ServerProjectilePlugin(),
        )