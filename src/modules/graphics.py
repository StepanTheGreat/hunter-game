import moderngl as gl
from app import Plugin, Schedule
from resources import Resources

CLEAR_COLOR = (0, 0, 0, 1)

class GraphicsContext:
    "The global ModernGL context. It should ONLY be initialized after the window is created"
    def __init__(self):
        self.ctx: gl.Context = gl.get_context()

    def get_context(self) -> gl.Context:
        return self.ctx
    
    def clear(self, color: tuple[int, ...]):
        self.ctx.clear(*color)

def clear_screen(resources: Resources):
    gfx = resources.get(GraphicsContext)
    gfx.clear(CLEAR_COLOR)
    
class GraphicsPlugin(Plugin):
    "A graphics plugin responsible for storing the graphics context and clearing the screen"
    def build(self, app):
        app.insert_resource(GraphicsContext(gl.get_context()))
        app.add_systems(Schedule.PreRender, clear_screen)
