from plugin import Plugin

from .interpolate import InterpolationSystemsPlugin
from .session import SessionSystemsPlugin

class ClientSystemsPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            InterpolationSystemsPlugin(),
            SessionSystemsPlugin()
        )