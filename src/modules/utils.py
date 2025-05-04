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