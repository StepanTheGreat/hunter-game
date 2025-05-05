"Common utiliy stuff"

from typing import Sequence, Iterable, TypeVar

I = TypeVar("I")
def sliding_window(sequence: Sequence[I], n: int) -> Iterable[I]:
    """
    Iterate over an iterable in `n` amount of steps, yielding the `n` amount of elements.
    If not enough elements - yields less.
    """

    assert n > 0

    for i in range(0, len(sequence), n):
        yield sequence[i:i+n]

class Timer:
    "A mini timer for time management"
    def __init__(self, interval: float, is_zero: bool):
        self.interval = interval
        self.on_interval = 0 if is_zero else interval

    def tick(self, dt: float):
        if self.on_interval > 0:
            self.on_interval -= dt

    def has_finished(self):
        return self.on_interval <= 0
    
    def reset(self):
        self.on_interval = self.interval

    def zero(self):
        "Make this clock act immediately. Only usefil in specific cases"
        self.on_interval = 0.

def clamp(x: int, mn: int, mx: int) -> int:
    "Clamp a number between a minimum and maximum"

    return max(min(x, mx), mn)