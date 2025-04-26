from collections import deque
from typing import Any

class CircleSet:
    """
    The idea behind a circle set is that its keys aren't permanent. They're added to a queue, where 
    when a limit is reached - the first key that was added to the set will be removed from the set.
    """
    def __init__(self, size: int):
        self.set = set()
        self.queue = deque()
        self.size = size

    def add(self, value: Any):
        "Add a new value to this recyclable set"
        self.queue.append(value)
        if len(self.queue) > self.size:
            self.set.remove(self.queue.popleft())

        self.set.add(value)

    def __contains__(self, value: Any):
        return value in self.queue
    
    def __len__(self) -> int:
        return len(self.set)