import moderngl as gl

from plugin import Plugin, Schedule
from resources import Resources

CLEAR_COLOR = (0, 0, 0, 1)

class GraphicsPlugin(Plugin):
    "A plugin responsible for managing a ModernGL context"

    "A graphics plugin responsible for storing the graphics context and clearing the screen"
    def build(self, app):
        app.insert_resource(GraphicsContext())
        app.add_systems(Schedule.PreRender, clear_screen)

class GraphicsContext:
    "The global ModernGL context and screen"
    def __init__(self):
        self.ctx: gl.Context = gl.get_context()

    def get_context(self) -> gl.Context:
        return self.ctx
    
    def clear(self, color: tuple[int, ...]):
        self.ctx.clear(*color)

def clear_screen(resources: Resources):
    resources[GraphicsContext].clear(CLEAR_COLOR)