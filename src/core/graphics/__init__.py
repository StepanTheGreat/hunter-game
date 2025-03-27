"A core module responsible for everything related to graphics, geometry and so on"

from plugin import Plugin

from .objects import *
from .camera import *
from .text import *
from .ctx import *

from .render2d import *
from .sprite import *
from .render3d import *

class GraphicsPlugin(Plugin):
    "A plugin responsible for managing a ModernGL context"

    "A graphics plugin responsible for storing the graphics context and clearing the screen"
    def build(self, app):
        app.add_plugins(
            GraphicsContextPlugin(),
            CameraPlugin(),
            TextPlugin(),
            Renderer3DPlugin(),
            SpriteRendererPlugin(),
            Renderer2DPlugin()
        )