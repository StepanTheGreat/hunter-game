from plugin import Plugin

from .clientlist import ClientListPlugin
from .broadcaster import ServerBroadcasterPlugin
from .state import GameStatePlugin
from .include import IncludedServicesPlugin

class ServerServicesPlugin(Plugin):
    def build(self, app):
        print("Building included plugins")
        app.add_plugins(
            IncludedServicesPlugin(),
            ClientListPlugin(),
            ServerBroadcasterPlugin(),
            GameStatePlugin()
        )