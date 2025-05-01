from plugin import Plugin, Schedule, Resources
from .rpcs import CLIENT_HOST_RPCS, CLIENT_ONLY_RPCS

class ClientPlugin(Plugin):
    def build(self, app):
        pass