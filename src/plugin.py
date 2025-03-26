"""
An application management module. Everything related to application modularisation:
- Plugins (small packages that can register custom logic to the app)
- Systems (custom logic that can get executed at different schedules)
- Resources (global unique resources that can be accessed from a type interface)
- Events and Event listeners (Custom structures that can be sent accross the app and respectively listened to)
"""

from enum import Enum, auto
from typing import Callable, TypeVar, Optional, Type

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

        assert getattr(event, "__app_event", False), "Only event objects can be pushed. Did you decorate it with the @event decorator?"
        
        self.queue.append(event)

    def read_events(self) -> list:
        "Get the internal event queue. The direction is from left (first) to right (last)"
        return self.queue

    def clear_events(self):
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

    def insert(self, item: R):
        "Insert a new resource, or overwrite an existing one of this type"
        self.database[type(item)] = item
    
    def get(self, ty: Type[R]) -> Optional[R]:
        "Get an item by its type. If not present - will return None"
        assert type(ty) is type

        return self.database.get(ty)

    def __getitem__(self, ty: Type[R]) -> R:
        assert type(ty) is type
        
        return self.database[ty]

    def remove(self, ty: Type[R]) -> Optional[R]:
        "Remove and possibly return a value of the provided type from the storage"
        assert type(ty) is type
        
        ret = self.get(ty)

        if not ret is None:
            del self.database[ty]

        return ret

class Schedule(Enum):
    "A schedule enum with different stages for system assigning"

    Startup = auto()
    "At the start of the app. Useful for initialisation"

    First = auto()
    "The first thing that ever gets executed at the start of the frame. This is solely used for clocks"

    PreUpdate = auto()
    "Preparation stage for the `Update` schedule. Should not be used for logic"

    Update = auto()
    "Main application logic schedule. Use it for most cases"

    PostUpdate = auto()
    "Operations like physics updates and so on that are supposed to take action after the update phase"

    PreRender = auto()
    "A stage before rendering. This is used internally for clearing the screen and overal preparation"

    Render = auto()
    "The main rendering stage where a user submits their commands"

    PostRender = auto()
    "All render requests are flushed"

    Last = auto()
    "The last screen that gets run in the frame. This is internally used to flip the screen contents"

    Finalize = auto()
    "At the end of the app. Useful for final cleanup"

class Plugin:
    def build(self, app: "AppBuilder"):
        "A plugin's custom registration logic"

class AppBuilder:
    def __init__(self, *plugins: Plugin):
        self.systems: dict[Schedule, list[Callable[[Resources]]]] = {}
        self.event_listeners: dict[type, list[Callable[[Resources, object]]]] = {}
        self.resources: Resources = Resources()
        self.runner = None

        self.add_plugins(*plugins)

    def add_plugins(self, *plugins: Plugin):
        for plugin in plugins:
            plugin.build(self)

    def get_resources(self) -> Resources:
        "If you need some manual control"
        return self.resources
    
    def get_resource(self, ty: Type[R]) -> R:
        return self.resources.get(ty)

    def insert_resource(self, resource):
        "Insert a resource into resources. If a resource of this type already is present - it will get overwritten"
        self.resources.insert(resource)

    def remove_resource(self, resource: type):
        "Remove a resource from the resources"
        self.resources.remove(resource)
    
    def add_systems(self, schedule: Schedule, *systems: Callable[[Resources], None]):
        "Add to this schedule a number of executable systems. Each of them takes a `Storage` object as their first argument"
        systems_list = self.systems.get(schedule)

        if systems_list is None:
            self.systems[schedule] = list(systems)
        else:
            systems_list += systems
        
    def add_event_listener(self, event_id: int, listener: Callable[[Resources, object], None]):
        "Add an event listener to the provided event ID"
        listeners_list = self.event_listeners.get(event_id)

        if listeners_list is None:
            self.event_listeners[event_id] = [listener]
        else:
            listeners_list.append(listener)

    def set_runner(self, runner: Callable[["App"], None]):
        """
        A runner is a function that's going to run the application. Different windowing backend have
        different mainloop implementation, thus a runner allows adapting to a specific backend.
        """
        self.runner = runner
    
R = TypeVar("R")

class App:
    "The main executor of all systems, event handlers. It also keeps resources, of course."
    def __init__(self, app_builder: AppBuilder):
        assert app_builder.runner is not None, "No runner function was provided to the application"

        self.runner = app_builder.runner
        self.systems: dict[Schedule, Callable[[Resources], None]] = app_builder.systems
        self.event_listeners: dict[int, Callable[[Resources, object], None]] = app_builder.event_listeners
        self.resources: Resources = app_builder.resources

        # Initialize the event writer
        self.resources.insert(EventWriter())

    def get_resource(self, resource: Type[R]) -> Optional[R]:
        "A shortcut for `app.get_resources().get(R)`"
        return self.resources.get(resource)
    
    def get_resources(self) -> Resources:
        return self.resources
    
    def __push_event(self, event):        
        for event_listener in self.event_listeners.get(event, []):
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

        # Execute the first schedule
        self.__execute_schedules(Schedule.First)

        # Read all the events received
        ewriter = self.resources[EventWriter]
        for event in ewriter.read_events():
            self.__push_event(event)

        ewriter.clear_events()

        # Continue all the other schedules like PreUpdate and Update
        self.__execute_schedules(Schedule.PreUpdate, Schedule.Update, Schedule.PostUpdate)

        # This approach can have huge benefits in systems that need to fetch some data and immediately
        # let other event listeners respond to it without 1-frame delay (like networking).
    
    def render(self):
        "Execute all render systems"
        self.__execute_schedules(
            Schedule.PreRender,
            Schedule.Render,
            Schedule.PostRender,
            Schedule.Last
        )
    
    def finalize(self):
        "Execute all finalize systems"
        self.__execute_schedules(Schedule.Finalize)

    def run(self):
        "Run the application by starting the runner function. This function should be called only once."
        self.runner(self)
