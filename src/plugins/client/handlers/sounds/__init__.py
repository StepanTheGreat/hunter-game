from plugin import Plugin, Schedule, Resources

from .projectile import ProjectileSoundHandlersPlugin

class SoundHandlersPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            ProjectileSoundHandlersPlugin()
        )