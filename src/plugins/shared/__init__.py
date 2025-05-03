from plugin import Plugin

from .entities import EntitiesPlugin
from .collisions import CollisionsPlugin
from .network import NetworkPlugin
from .components import CommonComponentsPlugin

class SharedPluginCollection(Plugin):
    "Plugins shared between both the server and the client"
    def build(self, app):
        app.add_plugins(
            CommonComponentsPlugin(),
            CollisionsPlugin(),
            NetworkPlugin(),
            EntitiesPlugin()
        )
