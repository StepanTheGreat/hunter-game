"""
An application management module. Everything related to application modularisation:
- Plugins (small packages that can register custom logic to the app)
- Systems (custom logic that can get executed at different schedules)
- Resources (global unique resources that can be accessed from a type interface)
- Events and Event listeners (Custom structures that can be sent accross the app and respectively listened to)
"""

from enum import Enum, auto
from typing import Callable, TypeVar, Optional

from pygame import Event


def event(cls):
    "An event decorator for event objects. It allows them to be sent or listened to across the entire application"
    cls.__app_event = True
    return cls

class EventWriter:
    "A built-in event writer for the entire app. It's automatically managed by the app"
    def __init__(self):
        self.queue: list = []

    def push_event(self, event):
        "Push an event onto the queue"

        assert event is not None, "Can't push None values"
        assert getattr(event, "__app_event", False), "Only event objects can be pushed"
        
        self.queue.append(event)

    def __read_events(self) -> list:
        "Get the internal event queue. The direction is from left (first) to right (last)"
        return self.queue

    def __clear_events(self):
        "Clear the internal queue. This should be called at the start of every frame internally by the app"
        self.queue.clear()  

# This is a generic argument that stands for Resource.
# It's highly useful because it allows the intellisense to understand arguments and return types, which
# isn't possible with type erasure. For example:
#
# func(arg: T) -> T
#
# Will tell the intellisense that any type that I use in my argument, will also be returned by the function. 
R = TypeVar("R")

class Resources:
    """
    Inspired by ECS Resources, a storage can store arbitrary values by their types. 
    It's a unique storage, thus only one item of a specific type can be stored at the same time.
    """
    def __init__(self, *resources: any):
        self.database = {}

        for res in resources:
            self.database[type(res)] = res

    def __assert_only_types(self, ty: any):
        assert type(ty) is type, "Storage.get can only accept types, not objects"

    def insert(self, item: R):
        "Insert a new resource, or overwrite an existing one of this type"
        self.database[type(item)] = item
    
    def get(self, ty: R) -> Optional[R]:
        "Get an item by its type. If not present - will return None"
        self.__assert_only_types(ty)

        return self.database.get(ty)

    def __getitem__(self, ty: R) -> R:
        self.__assert_only_types(ty)
        
        return self.database[ty]

    def remove(self, ty: R) -> Optional[R]:
        "Remove and possibly return a value of the provided type from the storage"
        self.__assert_only_types(ty)
        ret = self.get(ty)

        if not ret is None:
            del self.database[ty]

        return ret

class Schedule(Enum):
    "A schedule enum with different stages for system assigning"

    Startup = auto(),
    "At the start of the app. Useful for initialisation"

    First = auto(),
    "The first thing that ever gets executed at the start of the frame. This is solely used for clocks"

    PreUpdate = auto(),
    "Preparation stage for the `Update` schedule. Should not be used for logic"
    Update = auto(),
    "Main application logic schedule. Use it for most cases"

    PreRender = auto(),
    "A stage before rendering. This is used internally for clearing the screen and overal preparation"
    Render = auto(),
    "The main rendering stage where a user submits their commands"
    PostRender = auto()
    "All render requests are flushed and applied to the screen"

    Finalize = auto()
    "At the end of the app. Useful for final cleanup"

class Plugin:
    def build(self, app: "AppBuilder"):
        "A plugin's custom registration logic"

class AppBuilder:
    def __init__(self, *plugins: Plugin):
        self.systems: dict[Schedule, list[Callable[[Resources]]]] = {}
        self.event_listeners: dict[type, list[Callable[[Resources, Event]]]] = {}
        self.resources: Resources = Resources()

        for plugin in plugins:
            self.add_plugin(plugin)

    def add_plugins(self, *plugins: Plugin):
        for plugin in plugins:
            plugin.build(self)

    def insert_resource(self, resource):
        "Insert a resource into resources"
        self.resources.insert(resource)

    def remove_resource(self, resource: type):
        "Remove a resource from the resources"
        self.resources.remove(resource)
    
    def add_systems(self, schedule: Schedule, *systems: Callable[[Resources], None]):
        "Add to this schedule a number of executable systems. Each of them takes a `Storage` object as their first argument"
        systems_list = self.systems.get(schedule)

        if systems_list is None:
            self.systems[schedule] = [systems]
        else:
            systems_list += systems
        
    def add_event_listener(self, event_id: int, listener: Callable[[Resources, Event], None]):
        "Add an event listener to the provided event ID"
        listeners_list = self.event_listeners.get(event_id)

        if listeners_list is None:
            self.event_listeners[event_id] = [listener]
        else:
            listeners_list.append(listener)
    
R = TypeVar("R")

class App:
    "The main executor of all systems, event handlers. It also keeps resources, of course."
    def __init__(self, app_builder: AppBuilder):
        self.systems: dict[Schedule, Callable[[Resources], None]] = app_builder.systems
        self.event_listeners: dict[int, Callable[[Resources, Event], None]] = app_builder.event_listeners
        self.resources: Resources = app_builder.resources

        # Initialize the event writer
        self.resources[EventWriter] = EventWriter()

    def get_resource(self, resource: R) -> Optional[R]:
        return self.resources.get(resource)
    
    def __push_event(self, event):        
        for event_listener in self.event_listeners.get(event.type, []):
            event_listener(self.resources, event)

    def __execute_schedules(self, *schedules: Schedule):
        "Execute all systems in a schedule"
        for schedule in schedules:
            for system in self.systems.get(schedule, []):
                system(self.resources)

    def startup(self):
        "Execute all startup systems"
        self.__execute_schedules(Schedule.Startup)

    def update(self):
        "Execute all update systems"

        self.__execute_schedules(Schedule.First)

        event_writer = self.resources[EventWriter]
        for event in event_writer.__read_events():
            self.__push_event(event)

        event_writer.__clear_events()

        self.__execute_schedules(Schedule.PreUpdate,Schedule.Update)
    
    def render(self):
        "Execute all render systems"
        self.__execute_schedules(
            Schedule.PreRender,
            Schedule.Render,
            Schedule.PostRender
        )
    
    def finalize(self):
        "Execute all finalize systems"
        self.__execute_schedules(Schedule.Finalize)  
