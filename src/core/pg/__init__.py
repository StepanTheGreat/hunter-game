"A pygame backend plugin"
import pygame as pg

from typing import Union, Any
from plugin import App, AppBuilder, Resources, Plugin, EventWriter, event

from .events import *

pg.font.init()

from app_config import CONFIG

VIDEO_FLAGS = pg.OPENGL | pg.DOUBLEBUF | pg.RESIZABLE

@event
class PygameEvent:
    "Basically the same as `pygame.Event`, but registered for all pygame events that don't have a direct mapping"
    def __init__(self, event: pg.event.Event):
        self.type = event.type
        self.dict = event.dict

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

class Clock:
    "A general time keeping structure that automatically manages clock execution"
    def __init__(self, fps: int, fixed_fps: int):
        self.clock = pg.time.Clock()
        self.fps = fps
        self.fixed_fps = fixed_fps

        self.alpha_timer = 0
        self.fixed_updates = 0

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

        self.alpha_timer += delta_time
        self.fixed_updates = int(self.alpha_timer/self.get_fixed_delta())
        self.alpha_timer -= self.get_fixed_delta()*self.fixed_updates
        
        self.ticks += 1

    def get_fixed_delta(self) -> float:
        return 1/self.fixed_fps
    
    def get_alpha(self) -> float:
        """
        Alpha is the fraction that represents the current position of the visual frame 
        between last fixed step and the current one. It is measured between 0 and 1, where 0 is the last frame and
        1 is the current one.

        This is highly used in interpolation, since physics updates are separate from visual updates.
        """
        return max(0, min(self.alpha_timer/self.get_fixed_delta(), 1))
    
    def get_fixed_updates(self) -> int:
        "Tells how many fixed updates there should be for this tick"
        return self.fixed_updates

    def get_delta(self) -> float:
        "Get the amount of time that passed since last frame. Preferable over `get_ticks`"
        return self.delta_time
    
    def get_execution_time(self) -> float:
        return self.time
    
    def get_ticks(self) -> int:
        return self.ticks
    
    def get_fps(self) -> float:
        return self.clock.get_fps()
    
def update_sceen_size(resources: Resources, event: WindowResizeEvent):
    resources[Screen].update_resolution(event.new_width, event.new_height)

def pygame_runner(app: App):
    event_writer = app.get_resource(EventWriter)
    event_map = app.get_resource(PygameEventMap)
    clock = app.get_resource(Clock)
    should_quit = False

    app.startup()

    while not should_quit:
        clock.update()

        for event in pg.event.get():
            if event.type != pg.QUIT:
                event_writer.push_event(
                    event_map.map_event(event)
                )
            else:
                should_quit = True

        app.update(clock.get_fixed_updates())
        app.render()
        
        pg.display.flip()

    app.finalize()
    pg.quit()

class PygamePlugin(Plugin):
    def build(self, app):
        app.insert_resource(PygameEventMap())
        app.insert_resource(Screen(CONFIG.width, CONFIG.height, CONFIG.title, VIDEO_FLAGS, CONFIG.vsync))
        app.insert_resource(Clock(CONFIG.fps, CONFIG.fixed_fps))
        app.set_runner(pygame_runner)

        add_pygame_event_maps(
            app,
            (pg.MOUSEMOTION, MouseMotionEvent),
            (pg.VIDEORESIZE, WindowResizeEvent),
            (pg.MOUSEBUTTONDOWN, MouseButtonDownEvent),
            (pg.MOUSEBUTTONUP, MouseButtonUpEvent)
        )

        app.add_event_listener(WindowResizeEvent, update_sceen_size)