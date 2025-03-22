from plugin import Plugin

from .map import MapPlugin
from .render import MapRendererPlugin

class PluginsCollection(Plugin):
    def build(self, app):
        app.add_plugins(MapPlugin(), MapRendererPlugin())
