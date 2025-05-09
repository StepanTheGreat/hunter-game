from plugin import Plugin

from .graphics import GraphicsPlugin
from .entities import ClientEntitiesPlugin
from .scenes import ScenesPlugin
from .gui import GUIPlugin
from .perspective import PerspectivePlugin
from .actions import ClientActionPlugin
from .services.session import SessionPlugin

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

            GraphicsPlugin(),
            ClientEntitiesPlugin(),
            GUIPlugin(),
            ScenesPlugin(),
            PerspectivePlugin(),
            ClientActionPlugin(),
            SessionPlugin()
        )

        app.add_plugins(ServerManagementPlugin())
