from enum import Enum, auto
from typing import Callable, TypeVar, Optional
from resources import Resources

from pygame import Event

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
        "A plugins custom functionality registration to the app"

class AppBuilder:
    def __init__(self, *plugins: Plugin):
        self.systems: dict[Schedule, list[Callable[[Resources, Event]]]] = {}
        self.event_handlers: dict[int, list[Callable[[Resources]]]] = {}
        self.resources: Resources = Resources()

        for plugin in plugins:
            self.add_plugin(plugin)

    def add_plugin(self, plugin: Plugin):
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
            self.systems[schedule] = systems
        else:
            systems_list += systems
        
    def add_event_handler(self, event_id: int, callback: Callable[[Resources, Event], None]):
        "Add an event listener to the provided event ID"
        systems_list = self.systems.get(event_id)

        if systems_list is None:
            self.systems[event_id] = [callback]
        else:
            systems_list.append(callback)
    
R = TypeVar("R")

class App:
    "An app is the main "
    def __init__(self, app_builder: AppBuilder):
        self.systems: dict[Schedule, Callable[[Resources], None]] = app_builder.systems
        self.event_handlers: dict[int, Callable[[Resources, Event], None]] = app_builder.event_handlers
        self.resources: Resources = app_builder.resources

    def get_resource(self, resource: R) -> Optional[R]:
        return self.resources.get(resource)
    
    def push_event(self, event: Event):
        event_handlers = self.event_handlers.get(event.type)

        if event_handlers is not None:
            for event_handler in event_handlers:
                event_handlers(self.resources, event)

    def __execute_schedules(self, *schedules: Schedule):
        "Execute all systems in a schedule"
        for schedule in schedules:
            for system in self.systems.get(schedule, ()):
                system(self.resources)

    def startup(self):
        "Execute all startup systems"
        self.__execute_schedules(Schedule.Startup)

    def update(self):
        "Execute all update systems"
        self.__execute_schedules(
            Schedule.First,
            Schedule.PreUpdate,
            Schedule.Update
        )
    
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
    

    