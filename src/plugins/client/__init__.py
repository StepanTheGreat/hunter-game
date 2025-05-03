from plugin import Plugin

from .graphics import GraphicsPlugin
from .entities import ClientEntitiesPlugin
from .components import ClientCommonComponentsPlugin
from .scenes import ScenesPlugin
from .gui import GUIPlugin
from .perspective import PerspectivePlugin

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
            PerspectivePlugin()
        )
