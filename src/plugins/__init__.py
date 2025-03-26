from plugin import Plugin

from .map import MapPlugin
from .render import RenderPlugin
from .entities import EntitiesPlugin

class PluginsCollection(Plugin):
    def build(self, app):
        app.add_plugins(
            MapPlugin(), 
            RenderPlugin(),
            EntitiesPlugin()
        )
