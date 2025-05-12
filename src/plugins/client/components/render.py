from modules.inteprolation import Interpolated, InterpolatedDegrees, compute_time_alpha
from plugins.shared.components import *

@component
class RenderPosition:
    """
    A render position is an interpolated physics position. Because fixed ticks are independent from
    the frame rate, and thus it's possible for us to render more frequently than update physics - we must
    interpolate our positions to avoid the lag. That's exactly what render components are about
    """

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
    "Essentially the same as RenderPosition, but for angles"
    def __init__(self):
        self.angles = InterpolatedDegrees(0)
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
        alpha = compute_time_alpha(prelast, last, current_time)

        return self.interpolated.get_interpolated(alpha)

@component
class InterpolatedAngle:
    """
    Essentially the same as `InterpolatedPosition`, but for angles (directions)
    """
    def __init__(self):
        self.interpolated = InterpolatedDegrees(0)

        self.time: tuple[float, float] = (0, 0)
        "The time used when interpolating. It gets swapped every time a new position gets introduced."

    def push_angle(self, time: float, new_angle: float):
        self.interpolated.push_value(new_angle)

        self.time = (self.time[-1], time)

    def get_interpolated(self, current_time: float) -> float:
        prelast, last = self.time

        alpha = compute_time_alpha(prelast, last, current_time)

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