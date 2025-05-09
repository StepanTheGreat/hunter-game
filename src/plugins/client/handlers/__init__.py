from plugin import Plugin

from .session import SessionHandlersPlugin

class ClientHandlersPlugin(Plugin):
    def build(self, app):
        app.add_plugins(SessionHandlersPlugin())