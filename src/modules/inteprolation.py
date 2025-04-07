from typing import TypeVar, Generic
from numpy import pi

V = TypeVar("V")

class Interpolated(Generic[V]):
    """
    A really simple value container that allows managing interpolation between 2 values.
    Only values that allow for arithmetic operations (addition, subtraction and multiplication) can be used.
    """
    def __init__(self, initial: V):
        self.values: tuple[V, V] = (initial, initial)

    def push_value(self, new: V):
        "Add this value as the latest value."
        self.values = (self.values[1], new)

    def get_value(self) -> V:
        "Return the actual, non-interpolated value from the container"
        return self.values[-1]

    def get_interpolated(self, alpha: float) -> V:
        "Get the interpolated version between the 2 most actual values"
        assert 0 <= alpha <= 1
        return self.values[0] + (self.values[1]-self.values[0]) * alpha
    
class InterpolatedAngle(Interpolated):
    "An interpolation datatype specifically made for interpolating angles between -PI and PI"
    def __init__(self, initial: float):
        super().__init__(initial)

    def get_interpolated(self, alpha: float):
        assert 0 <= alpha <= 1

        delta_angle = self.values[1]-self.values[0]

        if delta_angle > pi:
            delta_angle -= 2*pi
        elif delta_angle < -pi:
            delta_angle += 2*pi
        
        interpolated = self.values[0] + delta_angle*alpha

        if interpolated > pi:
            interpolated -= 2*pi
        elif interpolated < -pi:
            interpolated += 2*pi

        return interpolated