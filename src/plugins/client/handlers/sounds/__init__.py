from plugin import Plugin, Schedule, Resources

from .projectile import ProjectileSoundHandlersPlugin
from .diamond import DiamondSoundHandlersPlugin
from .characters import CharactersSoundHandlersPlugin

class SoundHandlersPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            ProjectileSoundHandlersPlugin(),
            DiamondSoundHandlersPlugin(),
            CharactersSoundHandlersPlugin()
        )