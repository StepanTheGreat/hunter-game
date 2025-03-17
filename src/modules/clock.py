import pygame as pg
import plugin, resources

class ClockPlugin(plugin.Plugin):
    def __init__(self, fps: int):
        self.fps = fps

    def build(self, app):
        app.insert_resource(Clock(self.fps))
        app.add_systems(plugin.Schedule.First, update_time)

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
    
def update_time(resources: resources.Resources):
    resources[Clock].update()