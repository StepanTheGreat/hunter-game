import pygame as pg
from plugin import Resources, EventWriter, event, QuitEvent, Plugin, Schedule

from main import AppConfig

VIDEO_FLAGS = pg.OPENGL | pg.DOUBLEBUF

class Window:
    "A resource containing a pygame window. It's of no use of course, besides updating the screen and providing a GL context."
    def __init__(self, conf: AppConfig):
        pg.display.set_caption(conf.title)
        self.window = pg.display.set_mode((conf.width, conf.height), vsync=conf.vsync, flags = VIDEO_FLAGS)

@event
class PygameEvent:
    "A pygame event container"
    def __init__(self, event: pg.Event):
        self.event = event

def poll_pygame_events(resources: Resources):
    "Collect and resend all pygame events accross the app"
    print("Polling!")
    ewriter = resources[EventWriter]
    for event in pg.event.get():
        event = event if event.type != pg.QUIT else QuitEvent()
        ewriter.push_event(event)

def flip_pygame_display(_):
    "Flip the contents of the screen at the end of the frame"
    pg.display.flip()

def quit_pygame(_):
    "Gracefully quit pygame after quitting the app"
    pg.quit()

class WindowPlugin(Plugin):
    def __init__(self, conf: AppConfig):
        self.conf = conf
        
    def build(self, app):
        app.insert_resource(Window(self.conf))

        app.add_systems(Schedule.First, poll_pygame_events)
        app.add_systems(Schedule.Last, flip_pygame_display)
        app.add_systems(Schedule.Finalize, quit_pygame)