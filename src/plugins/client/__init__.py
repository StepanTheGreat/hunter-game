from plugin import Plugin

from .graphics import GraphicsPlugin
from .entities import ClientEntitiesPlugin
from .scenes import ScenesPlugin
from .gui import GUIPlugin
from .perspective import PerspectivePlugin
from .actions import ClientActionPlugin
from .session import SessionPlugin

from plugins.server import ServerManagementPlugin

from plugins.shared import SharedPluginsCollection

class ClientPluginCollection(Plugin):
    def build(self, app):
        app.add_plugins(
            SharedPluginsCollection(),
            GraphicsPlugin(),
            ClientEntitiesPlugin(),
            GUIPlugin(),
            ScenesPlugin(),
            PerspectivePlugin(),
            ClientActionPlugin(),
            SessionPlugin()
        )

        app.add_plugins(ServerManagementPlugin())
