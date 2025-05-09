from plugin import Plugin

from .scenes import ScenesPlugin
from .actions import ClientActionPlugin

from .systems import ClientSystemsPlugin
from .handlers import ClientHandlersPlugin
from .services import ClientServicesPlugin

from plugins.server import ServerManagementPlugin

from plugins.shared import SharedPluginsCollection

class ClientPluginCollection(Plugin):
    def build(self, app):
        app.add_plugins(
            SharedPluginsCollection(),

            ClientSystemsPlugin(),
            ClientHandlersPlugin(),
            ClientServicesPlugin(),

            ScenesPlugin(),
            ClientActionPlugin(),
        )

        app.add_plugins(ServerManagementPlugin())
