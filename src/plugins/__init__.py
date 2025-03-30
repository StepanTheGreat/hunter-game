from plugin import Plugin

from .graphics import GraphicsPlugin
from .entities import EntitiesPlugin
from .scenes import ScenesPlugin

class PluginsCollection(Plugin):
    def build(self, app):
        app.add_plugins(
            GraphicsPlugin(),
            EntitiesPlugin(),
            ScenesPlugin()
        )
