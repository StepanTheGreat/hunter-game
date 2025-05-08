from plugin import Plugin

from .player import PlayerPlugin
<<<<<<< HEAD
from .robber import RobberPlugin
from .policeman import PolicemanPlugin
=======
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
from .projectile import ProjectilePlugin
from .weapon import WeaponPlugin
from .diamond import DiamondPlugin

class EntitiesPlugin(Plugin):
    "Not to be confused with the core EntityPlugin, this is just a collection of ingame entities"
    def build(self, app):
        app.add_plugins(
            PlayerPlugin(),
<<<<<<< HEAD
            RobberPlugin(),
            PolicemanPlugin(),
=======
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
            ProjectilePlugin(),
            WeaponPlugin(),
            DiamondPlugin()
        )