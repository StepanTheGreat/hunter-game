from modules.inteprolation import Interpolated, InterpolatedAngle
from plugins.shared.components import *

@component
class RenderPosition:
    def __init__(self):
        self.positions = Interpolated(pg.Vector2(0, 0))
        self.interpolated = self.positions.get_value()

    def set_position(self, x: float, y: float):
        self.positions.push_value(pg.Vector2(x, y))

    def interpolate(self, alpha: float):
        self.interpolated = self.positions.get_interpolated(alpha)

    def get_position(self) -> pg.Vector2:
        return self.interpolated

@component
class RenderAngle:
    def __init__(self):
        self.angles = InterpolatedAngle(0)
        self.interpolated = self.angles.get_value()

    def interpolate(self, alpha: float):
        self.interpolated = self.angles.get_interpolated(alpha)

    def set_angle(self, new_angle: float):
        self.angles.push_value(new_angle)

    def get_angle(self) -> float:
        return self.interpolated    
    
    def get_vector(self) -> pg.Vector2:
        "Return this angle as a directional unit vector"
        return pg.Vector2(np.cos(self.interpolated), np.sin(self.interpolated))

@component
class InterpolatedPosition:
    """
    Because movement packets itroduce inherent jitter (as they can be delayed, they're sent way less
    frequently than the refresh rate or so on), this component is going to fix the problem by
    interpolating positions. Double interpolation right here! Essentially, when receiving movement
    packets - they should go directly to this component instead, which is going to interpolate entities.
    
    This component however shouldn't be applied to the client, as it controls their own movement
    without much jitter.
    """
    def __init__(self):
        self.interpolated = Interpolated(pg.Vector2(0, 0))

        self.time: tuple[float, float] = (0, 0)
        "The time used when interpolating. It gets swapped every time a new position gets introduced."

    def push_position(self, time: float, new_x: float, new_y: float):
        self.interpolated.push_value(pg.Vector2(new_x, new_y))
        self.time = (self.time[-1], time)

    def get_interpolated(self, current_time: float) -> pg.Vector2:
        prelast, last = self.time

        # We're computing the alpha here of our current time. Essentially, if we have 2 points in time
        # A and B, and we have time C in between these time points, we would like to get a value
        # between 0 and 1, which we could then use as alpha for our position interpolation.
        #
        # For this we first need to get the delta time between our current time and A (the oldest point).
        # Then, we're dividing this by the delta time between A and B.
        # So if for example A is 1, B is 2 and C is 1.5, then the formula will be:
        # (C-A)/(B-A) -> (1.5-1)/(2-1) -> 0.5/1 -> 0.5
        alpha = min(
            1, 
            max((current_time-prelast)/(last-prelast+0.0001), 0)
        )

        return self.interpolated.get_interpolated(alpha)
    

@component
class PerspectiveAttachment:
    """
    A perspective is a combination of both character's visual and audio perception. 
    It's both their camera and ears. The perspective attachment allows an entity to both 
    perceive and hear the surrounding around it. 
    """
    def __init__(self, height: float, priority: int):
        self.height = height
        self.priority = priority