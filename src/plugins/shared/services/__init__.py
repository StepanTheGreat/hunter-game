from plugin import Plugin

from .map import WorldMapPlugin
from .collisions import CollisionsPlugin
from .uidman import EntityUIDManagerPlugin
from .network import NetworkPlugin

class SharedServicesPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            WorldMapPlugin(),
            CollisionsPlugin(),
            EntityUIDManagerPlugin(),
            NetworkPlugin()
        )