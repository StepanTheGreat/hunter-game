from plugin import Plugin

from .base import BaseSystemsPlugin
from .diamond import DiamondSystemsPlugin
from .player import PlayerSystemsPlugin
from .projectile import ProjectileSystemsPlugin
from .weapon import WeaponSystemsPlugin

class SharedSystemsPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            BaseSystemsPlugin(),
            DiamondSystemsPlugin(),
            PlayerSystemsPlugin(),
            ProjectileSystemsPlugin(),
            WeaponSystemsPlugin()
        )