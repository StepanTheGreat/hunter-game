from plugin import Plugin

from .graphics import GraphicsPlugin
from .entities import EntitiesPlugin
from .scenes import ScenesPlugin
from .gui import GUIPlugin

class PluginsCollection(Plugin):
    def build(self, app):
        app.add_plugins(
            GraphicsPlugin(),
            EntitiesPlugin(),
            GUIPlugin(),
            ScenesPlugin(),
        )
