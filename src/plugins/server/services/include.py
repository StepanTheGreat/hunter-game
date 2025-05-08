from plugin import Plugin

from plugins.shared.services.network import Server, BroadcastWriter
from plugins.rpcs.server import SERVER_RPCS

from plugins.server.constants import MAX_PLAYERS

class IncludedServicesPlugin(Plugin):
    def build(self, app):
        app.insert_resource(BroadcastWriter())
        app.insert_resource(Server(app.get_resources(), MAX_PLAYERS, SERVER_RPCS))