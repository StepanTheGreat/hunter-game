from plugin import Plugin
from main import AppConfig

__all__ = [
    "graphics",
    "clock",
]

from .graphics import GraphicsPlugin
from .clock import ClockPlugin

class CoreModulesPlugin(Plugin):
    "The core application modules"
    def __init__(self, config: AppConfig):
        self.config = config

    def build(self, app):
        app.add_plugin(ClockPlugin(self.config.fps))
        app.add_plugin(GraphicsPlugin())