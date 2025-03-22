"A pygame backend plugin"
import pygame as pg
from plugin import App, Plugin, EventWriter, event

from main import AppConfig

VIDEO_FLAGS = pg.OPENGL | pg.DOUBLEBUF

@event
class PygameEvent:
    "A pygame event container"
    def __init__(self, event: pg.Event):
        self.event = event

class Clock:
    "A general time keeping structure that automatically manages clock execution"
    def __init__(self, fps: int):
        self.clock = pg.time.Clock()
        self.fps = fps

        self.ticks = 0
        self.delta_time = 0.0
        self.time = 0.0

    def update(self):
        """
        Update the internal time information with provided delta time. 
        This is only supposed to get called from the clock plugin
        """

        delta_time = self.clock.tick(self.fps)

        self.delta_time = delta_time
        self.time += delta_time
        self.ticks += 1

    def get_delta(self) -> float:
        "Get the amount of time that passed since last frame. Preferable over `get_ticks`"
        return self.delta_time
    
    def get_execution_time(self) -> float:
        return self.time
    
    def get_ticks(self) -> int:
        return self.ticks
    
    def get_fps(self) -> float:
        return self.clock.get_fps()

def pygame_runner(app: App):

    screen = pg.display.set_mode((640, 520), flags=VIDEO_FLAGS, vsync=True)
    resources = app.get_resources()
    ewriter = resources[EventWriter]
    should_quit = False

    while not should_quit:
        resources[Clock].update()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                should_quit = True
            else:
                ewriter.push_event(PygameEvent(event))

        app.update()
        app.render()
        
        pg.display.flip()

    app.finalize()
    pg.quit()

class PygamePlugin(Plugin):
    def __init__(self, config: AppConfig):
        self.config = config

    def build(self, app):
        app.insert_resource(Clock(self.config.fps))
        app.set_runner(pygame_runner)