import pygame as pg

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