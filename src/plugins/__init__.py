from plugin import Plugin

from .map import MapPlugin

class PluginsCollection(Plugin):
    def build(self, app):
        app.add_plugins(MapPlugin())