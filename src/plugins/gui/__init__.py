from plugin import Plugin

from .gui import *

class GUIPlugin(Plugin):
    def build(self, app):
        app.add_plugins(GUIManagerPlugin())
