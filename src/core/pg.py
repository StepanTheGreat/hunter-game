"A pygame backend plugin"
import pygame as pg
from plugin import App, Plugin, EventWriter, event

from app_config import CONFIG

VIDEO_FLAGS = pg.OPENGL | pg.DOUBLEBUF

@event
class PygameEvent:
    "Basically the same as `pygame.Event`, but registered as an app event"
    def __init__(self, event: pg.Event):
        self.type = event.type
        self.dict = event.dict

class Screen:
    "A pygame screen container. Pretty useless actually, but who knows?"
    def __init__(self):
        pg.display.set_caption(CONFIG.title)
        self.screen = pg.display.set_mode((CONFIG.width, CONFIG.height), flags=VIDEO_FLAGS, vsync=CONFIG.vsync) 

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

        delta_time = self.clock.tick(self.fps) / 1000

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
    event_writer = app.get_resource(EventWriter)
    clock = app.get_resource(Clock)
    should_quit = False

    app.startup()

    while not should_quit:
        clock.update()

        for event in pg.event.get():
            if event.type != pg.QUIT:
                event_writer.push_event(PygameEvent(event))
            else:
                should_quit = True

        app.update()
        app.render()
        
        pg.display.flip()

    app.finalize()
    pg.quit()

class PygamePlugin(Plugin):
    def build(self, app):
        app.insert_resource(Screen())
        app.insert_resource(Clock(CONFIG.fps))
        app.set_runner(pygame_runner)