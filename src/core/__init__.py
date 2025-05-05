"""
The core plugins module. It contains the **core** components of the application, like opengl context,
time, networking and so on. Child plugins will use these core components to render/queue/send or do anything they need.
"""

from plugin import Plugin
from app_config import CONFIG

from .graphics import GraphicsPlugin
from .pg import PygamePlugin
from .sound import SoundPlugin
from .input import InputPlugin
from .assets import AssetsPlugin
from .ecs import ECSPlugin
from .time import TimePlugin
from .telemetry import *

class ServerCoreModulesPlugin(Plugin):
    "Core modules used by the server"
    def build(self, app):
        app.add_plugins(
            AssetsPlugin(CONFIG.assets_dir),
            TimePlugin(),
            ECSPlugin()
        )

class ClientCoreModulesPlugin(Plugin):
    "The core application modules used solely by the client"
    def build(self, app):
        app.add_plugins(
            ServerCoreModulesPlugin(),
            PygamePlugin(),
            SoundPlugin(),
            InputPlugin(),
            GraphicsPlugin(),
            TelemetryPlugin(),
        )