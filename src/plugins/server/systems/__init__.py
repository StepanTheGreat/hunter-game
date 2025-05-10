from plugin import Plugin

from .base import BaseSystemsPlugin
from .sync import SyncSystemsPlugin
from .map import MapSystemsPlugin

class ServerSystemsPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            BaseSystemsPlugin(),
            SyncSystemsPlugin(),
            MapSystemsPlugin()
        )