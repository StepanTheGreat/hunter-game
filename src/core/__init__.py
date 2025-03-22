"""
The core plugins module. It contains the **core** components of the application, like opengl context,
time, networking and so on. Child plugins will use these core components to render/queue/send or do anything they need.
"""

from plugin import Plugin
from app_config import AppConfig

from .graphics import GraphicsPlugin
from .pg import PygamePlugin
from .assets import AssetsPlugin

class CoreModulesPlugin(Plugin):
    "The core application modules"
    def __init__(self, config: AppConfig):
        self.config = config

    def build(self, app):
        app.add_plugins(
            PygamePlugin(self.config),
            AssetsPlugin(self.config.assets_dir),
            GraphicsPlugin(),
        )