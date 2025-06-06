"A pygame backend plugin"
import pygame as pg

from typing import Union, Any
from plugin import App, AppBuilder, Resources, Plugin, EventWriter

from core.events.pg import *
from core.time import Clock

# Actually, don't ask me why this pre-init, I just found that it's better for general audio playback speed
pg.mixer.pre_init(44100, -16, 1, 512)

pg.font.init()

from app_config import CONFIG

VIDEO_FLAGS = pg.OPENGL | pg.DOUBLEBUF | pg.RESIZABLE

class PygameEventMap:
    """
    The purpose of this class is to map pygame events into app-specific events. Instead of `PygameEvent`
    (which is fired by default if there's no mapping for an event) - we can transform it into `MouseMotionEvent`,
    or any other more specific event. This achieves 2 things:

    1. It allows us, users, to easily define different event mappings for every event we require.
       Since pygame has a lot of events - we can overwrite only a specific amount of them.
    2. It makes every single event **specific**. Instead of constantly checking if an event is of type `MOUSEMOTION`,
       we can simply listen directly to `MouseMotionEvent` and avoid that check entirely.
    3. While not directly intented, but if we were  to listen for all possible pygame events - every single
       part of our app will get called for absolutely no reason. With this, we only call the parts that actually
       need to get called.  
    """
    def __init__(self):
        self.database = {}

    def add_mapping(self, pg_event_id: int, cls: type):
        "Add a custom event class under the provided pygame event ID"
        self.database[pg_event_id] = cls
    
    def map_event(self, event: pg.event.Event) -> Union[PygameEvent, Any]:
        "Try get a registered mapped event class or if not present - construct a normal PygameEvent"
        return self.database.get(event.type, PygameEvent)(event)
    
def add_pygame_event_maps(app: AppBuilder, *mappings: tuple[int, type]):
    "A utility function that allows you to easily define an unlimited number of pygame-user event mappings"
    event_map = app.get_resource(PygameEventMap)
    for pg_event_id, mapping_class in mappings:
        event_map.add_mapping(pg_event_id, mapping_class)

class Screen:
    "A pygame screen container. Pretty useless actually, but who knows?"
    def __init__(self, width: int, height: int, title: str, video_flags: int, vsync: bool):
        pg.display.set_caption(title)
        self.width = width
        self.height = height
        self.screen = pg.display.set_mode((self.width, self.height), flags=video_flags, vsync=vsync) 

    def get_size(self) -> tuple[int, int]:
        return self.width, self.height
    
    def get_width(self) -> int:
        return self.width
    
    def get_height(self) -> int:
        return self.height
    
    def update_resolution(self, new_width: int, new_height: int):
        "This method can only be called from the event listener when the screen resolution has changed"
        self.width, self.height = new_width, new_height

class ShouldQuit:
    "The sole purpose of this resource is to just let apps control when the app should quit"
    def __init__(self):
        self.quit: bool = False

    def queue_quit(self):
        self.quit = True

    def should_quit(self) -> bool:
        return self.quit

def pygame_runner(app: App):
    event_writer = app.get_resource(EventWriter)
    event_map = app.get_resource(PygameEventMap)
    clock = app.get_resource(Clock)
    should_quit = app.get_resource(ShouldQuit)
    caught_exception = None

    app.startup()

    try:
        while not should_quit.should_quit():
            clock.update()

            for event in pg.event.get():
                event_writer.push_event(
                    event_map.map_event(event)
                )

            app.update(clock.get_fixed_updates())
            app.render()
            
            pg.display.flip()
    except Exception as exception:
        
        # We don't want to handle events when an app has caught an exception - only finalize it
        event_writer.clear_events()

        caught_exception = exception
        print("The app has caught an exception, finalizing...")

    app.finalize()
    pg.quit()

    if caught_exception is not None:
        raise caught_exception
    
def update_sceen_size(resources: Resources, event: WindowResizeEvent):
    resources[Screen].update_resolution(event.new_width, event.new_height)

def on_quit_event(resources: Resources, _):
    resources[ShouldQuit].queue_quit()

class PygamePlugin(Plugin):
    def build(self, app):
        app.insert_resource(PygameEventMap())
        app.insert_resource(Screen(CONFIG.width, CONFIG.height, CONFIG.title, VIDEO_FLAGS, CONFIG.vsync))
        app.insert_resource(Clock(CONFIG.fps, CONFIG.fixed_fps))
        app.insert_resource(ShouldQuit())
        app.set_runner(pygame_runner)

        add_pygame_event_maps(
            app,
            (pg.QUIT, QuitEvent),
            (pg.MOUSEMOTION, MouseMotionEvent),
            (pg.VIDEORESIZE, WindowResizeEvent),
            (pg.MOUSEBUTTONDOWN, MouseButtonDownEvent),
            (pg.MOUSEBUTTONUP, MouseButtonUpEvent)
        )

        app.add_event_listener(WindowResizeEvent, update_sceen_size)
        app.add_event_listener(QuitEvent, on_quit_event)