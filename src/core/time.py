import pygame as pg

from typing import Callable, Optional, Union

from plugin import Plugin, Schedule, Resources, AppBuilder

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

class SystemScheduler:
    """
    This structure schedules execution of systems. Essentially it allows you to delay an execution
    of a system either in ticks or in seconds
    """

    class ScheduledSystemTimer:
        """
        This mini class simply keeps track of ticks and tells the outer class when it's time
        to execute the bound system.
        """

        def __init__(self, execute_in: Union[float, int], tick_based: bool, repeated: bool):
            assert execute_in > 0, "Don't schedule your systems for less than a tick..." 
            assert (tick_based and type(execute_in) is int) or not tick_based, "A system scheduled in ticks can only accept integer tick scheduling"

            self.tick_based: bool = tick_based
            "A timer based in ticks will behave differently compared to the one defined in time"

            self.execute_in: Union[float, int] = execute_in
            "The amount of ticks or time after which the scheduled system is going to get executed"

            self.repeat: Optional[Union[float, int]] = execute_in if repeated else None
            """
            A silly workaround, but if this function is repeating - we're going to store its usual
            delay time, but if it's a one-shot system - this will be `None`
            """

        def tick_and_check(self, dt: float) -> bool:
            "Tick this scheduled system and possibly execute it"

            # A system getting scheduled in ticks, will get decremented by 1. 
            # A system scheduled in seconds however, will get decremented by delta time
            dt = 1 if self.tick_based else dt
            
            should_execute = False

            self.execute_in -= dt
            if self.execute_in <= 0:
                should_execute = True

                if self.repeat is not None:
                    self.execute_in = self.repeat

            return should_execute

        def should_get_removed(self) -> bool:
            """
            Should this scheduled system get removed?
            A system will get removed if it already got executed and it's not repeating.
            """

            return self.execute_in <= 0 and self.repeat is None

    def __init__(self):
        self.scheduled_systems: dict[Callable, SystemScheduler.ScheduledSystemTimer] = {}

    def tick(self, resources: Resources, dt: float):
        """
        Tick and execute all scheduled systems bound to this scheduler. 
        All one-shot systems if executed will also get cleaned up.
        """

        removed_systems = []

        # For every system/timer pair, we're going to update it's timer and check if it can be executed
        for system, timer in self.scheduled_systems.items():
            if timer.tick_and_check(dt):
                # Yup, we can execute it
                system(resources)

                # If it's a one-shot system - we're going to clean it later
                if timer.should_get_removed():
                    removed_systems.append(system)

        # Clean all executed one-shot systems
        for removed_system in removed_systems:
            self.scheduled_systems.pop(removed_system)

    def schedule_ticks(self, system: Callable[[Resources], None], in_ticks: int, repeat: bool = False):
        "Schedule the provided system to get executed in the provided amount of fixed ticks"

        self.scheduled_systems[system] = SystemScheduler.ScheduledSystemTimer(in_ticks, True, repeat)

    def schedule_seconds(self, system: Callable[[Resources], None], in_time: float, repeat: bool = False):
        "Schedule the provided system to run in the provided amount of time"
        
        self.scheduled_systems[system] = SystemScheduler.ScheduledSystemTimer(in_time, False, repeat)

    def __contains__(self, system: Callable[[Resources], None]) -> bool:
        return system in self.scheduled_systems

    def remove_scheduled(self, system: Callable[[Resources], None]):
        "Remove the provided scheduled system if it's present"

        if system in self.scheduled_systems:
            self.scheduled_systems.pop(system)

def run_system_scheduler(resources: Resources):
    "Execute the scheduler and its bound systems"

    dt = resources[Clock].get_fixed_delta()
    resources[SystemScheduler].tick(resources, dt)

def schedule_systems_seconds(
    app: AppBuilder, 
    *entries: tuple[Callable[[Resources], None], float, bool]
):
    "An utility function that allows you to register sheduled systems inside plugin definitions"
    for system, time, repeat in entries:
        app.get_resource(SystemScheduler).schedule_seconds(system, time, repeat)

def schedule_systems_tics(
    app: AppBuilder, 
    *entries: tuple[Callable[[Resources], None], int, bool]
):
    "An utility function that allows you to register sheduled systems inside plugin definitions"
    for system, ticks, repeat in entries:
        app.get_resource(SystemScheduler).schedule_ticks(system, ticks, repeat)

class TimePlugin(Plugin):
    def build(self, app):
        app.insert_resource(SystemScheduler())
        app.add_systems(Schedule.FixedUpdate, run_system_scheduler)