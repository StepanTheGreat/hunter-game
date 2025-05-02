"""
Everything related to server-side logic, be it from managing the game session, to components, systems
and so on.
"""

from plugin import Plugin
from .session import ServerSessionPlugin

class ServerPlugin(Plugin):
    def build(self, app):
        app.add_plugins(ServerSessionPlugin())
