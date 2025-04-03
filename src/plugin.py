"""
An application management module. Everything related to application modularisation:
- Plugins (small packages that can register custom logic to the app)
- Systems (custom logic that can get executed at different schedules)
- Resources (global unique resources that can be accessed from a type interface)
- Events and Event listeners (Custom structures that can be sent accross the app and respectively listened to)
"""

from enum import Enum, auto
from typing import Callable, TypeVar, Optional, Type, Any

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

# Event
E = TypeVar("E")

class Resources:
    """
    Inspired by ECS Resources, a storage can store arbitrary values by their types. 
    It's a unique storage, thus only one item of a specific type can be stored at the same time.
    """
    def __init__(self, *resources: Any):
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
    
    def __contains__(self, ty: type) -> bool:
        return ty in self.database 

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

    PreDraw = auto()
    "A stage before drawing. This is used internally for clearing the screen and overal preparation"

    Draw = auto()
    "The main rendering stage where a user submits their commands"

    PostDraw = auto()
    "All render requests are flushed"

    Last = auto()
    "The last screen that gets run in the frame. This is internally used to flip the screen contents"

    Finalize = auto()
    "At the end of the app. Useful for final cleanup"

class Plugin:
    def build(self, app: "AppBuilder"):
        "A plugin's custom registration logic"

DEFAULT_PRIORITY = 0

class AppBuilder:
    def __init__(self, *plugins: Plugin):
        self.systems: dict[Schedule, dict[int, list[Callable[[Resources]]]]] = {}
        # When building systems, we're using a dictionary that sorts systems based on their
        # priorityy number. This is only a build-time concept though! When finalizing the build - it will sort
        # all systems and collect them into a unified list, where they will be all executed in their proper order!

        self.event_listeners: dict[type, list[Callable[[Resources, object]]]] = {}
        self.resources: Resources = Resources(
            EventWriter()
        )
        self.runner = None

        self.add_plugins(*plugins)

    def build_systems(self) -> dict[Schedule, list[Callable[[Resources], None]]]:
        """
        Sort all systems based on their priority into a single dictionary. This is only called once when
        finalizing the app.
        """

        # First we create a new dictionary
        ret_systems: dict[Schedule, list[Callable[[Resources]]]] = {}

        sort_key = lambda pair: pair[0]

        # Then we iterate every pair in our systems collection (that maps schedules to priority-systems maps)
        for schedule, priority_system_map in self.systems.items():

            # We will initialize an empty list for every schedule
            ret_systems[schedule] = []

            # In ascending order, we will add our systems to the list, based on their priority number
            for _, systems in sorted(priority_system_map.items(), key=sort_key):
                ret_systems[schedule] += systems

        return ret_systems

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
    
    def add_systems(self, schedule: Schedule, *systems: Callable[[Resources], None], priority: int = DEFAULT_PRIORITY):
        "Add to this schedule a number of executable systems. Each of them takes a `Storage` object as their first argument"
        if schedule not in self.systems:
            self.systems[schedule] = {}
        
        if priority not in self.systems[schedule]:
            self.systems[schedule][priority] = []
        
        self.systems[schedule][priority] += systems
        
    def add_event_listener(self, event_ty: Type[E], listener: Callable[[Resources, E], None]):
        "Add an event listener to the provided event ID"
        listeners_list = self.event_listeners.get(event_ty)

        if listeners_list is None:
            self.event_listeners[event_ty] = [listener]
        else:
            listeners_list.append(listener)

    def set_runner(self, runner: Callable[["App"], None]):
        """
        A runner is a function that's going to run the application. Different windowing backends have
        different mainloop implementation, thus a runner allows adapting to a specific backend.
        """
        self.runner = runner
    
R = TypeVar("R")

class App:
    "The main executor of all systems, event handlers. It also keeps resources, of course."
    def __init__(self, app_builder: AppBuilder):
        assert app_builder.runner is not None, "No runner function was provided to the application"

        self.runner = app_builder.runner
        self.systems: dict[Schedule, Callable[[Resources], None]] = app_builder.build_systems()
        self.event_listeners: dict[int, Callable[[Resources, object], None]] = app_builder.event_listeners
        self.resources: Resources = app_builder.resources

    def get_resource(self, resource: Type[R]) -> Optional[R]:
        "A shortcut for `app.get_resources().get(R)`"
        return self.resources.get(resource)
    
    def get_resources(self) -> Resources:
        return self.resources
    
    def __push_event(self, event):
        for event_listener in self.event_listeners.get(type(event), []):
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
            Schedule.PreDraw,
            Schedule.Draw,
            Schedule.PostDraw,
            Schedule.Last
        )
    
    def finalize(self):
        "Execute all finalize systems"
        self.__execute_schedules(Schedule.Finalize)

    def run(self):
        "Run the application by starting the runner function. This function should be called only once."
        self.runner(self)

def run_if(condition_func: Callable[[Resources], bool], *args):
    """
    A system decorator that controls whether to run a specific system or not. 
    
    The expected condition is a function that takes a class `Resources` as its first argument and an unlimited
    amount of additional arguments that will be used in the conditional function arguments.
    The condition function has to return either `True` or `False`, 
    where `True` means the execution of the underlying system.
    """
    def decorator(func):
        def conditional_system(resources: Resources):
            if condition_func(resources, *args):
                func(resources)

        return conditional_system

    return decorator

def resource_exists(resources: Resources, resource: type) -> bool:
    "A default conditional that runs when a specified resource exists"
    return resource in resources