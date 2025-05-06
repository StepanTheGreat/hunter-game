from plugin import Plugin

from .player import PlayerPlugin
from .robber import RobberPlugin
from .policeman import PolicemanPlugin
from .projectile import ProjectilePlugin
from .weapon import WeaponPlugin

class EntitiesPlugin(Plugin):
    "Not to be confused with the core EntityPlugin, this is just a collection of ingame entities"
    def build(self, app):
        app.add_plugins(
            PlayerPlugin(),
            RobberPlugin(),
            PolicemanPlugin(),
            ProjectilePlugin(),
            WeaponPlugin()
        )