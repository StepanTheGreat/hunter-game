from plugin import Plugin

from .player import PlayerPlugin
from .projectile import ProjectilePlugin
from .weapon import WeaponPlugin
from .diamond import DiamondPlugin

class EntitiesPlugin(Plugin):
    "Not to be confused with the core EntityPlugin, this is just a collection of ingame entities"
    def build(self, app):
        app.add_plugins(
            PlayerPlugin(),
            ProjectilePlugin(),
            WeaponPlugin(),
            DiamondPlugin()
        )