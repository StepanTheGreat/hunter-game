from plugin import Plugin

from .graphics import GraphicsPlugin
from .entities import ClientEntitiesPlugin
from .components import ClientCommonComponentsPlugin
from .scenes import ScenesPlugin
from .gui import GUIPlugin
from .perspective import PerspectivePlugin
from .actions import ClientActionPlugin
<<<<<<< HEAD
=======
from .session import SessionPlugin
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75

from plugins.server import ServerManagementPlugin

from plugins.shared import SharedPluginCollection

class ClientPluginCollection(Plugin):
    def build(self, app):
        app.add_plugins(
            SharedPluginCollection(),
            GraphicsPlugin(),
            ClientEntitiesPlugin(),
            ClientCommonComponentsPlugin(),
            GUIPlugin(),
            ScenesPlugin(),
            PerspectivePlugin(),
<<<<<<< HEAD
            ClientActionPlugin()
=======
            ClientActionPlugin(),
            SessionPlugin()
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
        )

        app.add_plugins(ServerManagementPlugin())
