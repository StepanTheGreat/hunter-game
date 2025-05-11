from plugin import Plugin, Schedule, Resources

from .projectile import ProjectileSoundHandlersPlugin
from .diamond import DiamondSoundHandlersPlugin

class SoundHandlersPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            ProjectileSoundHandlersPlugin(),
            DiamondSoundHandlersPlugin()
        )