from plugin import Plugin

from .graphics import GraphicsPlugin
from .entities import EntitiesPlugin
from .scenes import ScenesPlugin
from .gui import GUIPlugin
from .collisions import CollisionsPlugin

class PluginsCollection(Plugin):
    def build(self, app):
        app.add_plugins(
            CollisionsPlugin(),
            GraphicsPlugin(),
            EntitiesPlugin(),
            GUIPlugin(),
            ScenesPlugin(),
        )
