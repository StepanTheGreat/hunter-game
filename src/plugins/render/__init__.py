"Everything related to rendering the game world"

from plugin import Plugin

from .map import *
from .sprite import *

class RenderPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            MapRendererPlugin(),
            SpriteRendererPlugin()
        )