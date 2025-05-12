from plugin import Plugin

from .projectile import ProjectileSoundHandlersPlugin
from .diamond import DiamondSoundHandlersPlugin
from .characters import CharactersSoundHandlersPlugin
from .session import SessionSoundHandlersPlugin

class SoundHandlersPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            ProjectileSoundHandlersPlugin(),
            DiamondSoundHandlersPlugin(),
            CharactersSoundHandlersPlugin(),
            SessionSoundHandlersPlugin()
        )