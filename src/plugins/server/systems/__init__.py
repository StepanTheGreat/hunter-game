from plugin import Plugin

from .base import BaseSystemsPlugin
from .session import SessionSystemsPlugin

class ServerSystemsPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            BaseSystemsPlugin(),
            SessionSystemsPlugin()
        )