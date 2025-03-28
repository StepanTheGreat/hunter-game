from collections import deque
from typing import Any

class CircleSet:
    """
    The idea behind a circle set is that its keys aren't permanent. They're added to a queue, where 
    when a limit is reached - the first key that was added to the set will be removed from the set.

    For example, in a circle set of size 10, if we add these 10 keys:
    `0, 1, 2, 3, 4, 5, 6, 7, 8, 9`

    All of them will be present in the set, since they perfectly fit our key capacity. However, if we
    add a key... `10`:

    `1, 2, 3, 4, 5, 6, 7, 8, 9, 10`

    We see that `0` was removed! While it's pretty useless on a small scale - it does show itself great when
    we have thousands of different keys that we would like to rotate. This is highly useful in packets, since we would
    like to keep track of sequence numbers to know which packets were received. 
    However, sequence packets change all the time. How do we know which sequence numbers 
    are still and use and which are not? We could simply store all these sequence numbers in a queue, but then
    it will not have O(1) look-up complexity.

    This is not the best solution, and I'm free to discuss any better ones.
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