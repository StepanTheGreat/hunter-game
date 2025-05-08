from plugin import Plugin

from .services import SharedServicesPlugin
from .systems import SharedSystemsPlugin

class SharedPluginsCollection(Plugin):
    "Systems shared between both the server and the client"

    def build(self, app):
        app.add_plugins(
            SharedServicesPlugin(),
            SharedSystemsPlugin()
        )
