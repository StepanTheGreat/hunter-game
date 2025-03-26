"""
The core plugins module. It contains the **core** components of the application, like opengl context,
time, networking and so on. Child plugins will use these core components to render/queue/send or do anything they need.
"""

from plugin import Plugin
from app_config import CONFIG

from .graphics import GraphicsPlugin
from .pg import PygamePlugin
from .assets import AssetsPlugin
from .entity import EntityPlugin
from .collisions import CollisionsPlugin

class CoreModulesPlugin(Plugin):
    "The core application modules"
    def build(self, app):
        app.add_plugins(
            PygamePlugin(),
            AssetsPlugin(CONFIG.assets_dir),
            GraphicsPlugin(),
            EntityPlugin(),
            CollisionsPlugin()
        )