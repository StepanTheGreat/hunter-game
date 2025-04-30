import numpy as np

from typing import Any, Union

class NumpyList:
    def __init__(self, data: list[Any] = [], dtype = None, reserve: int = 1):
        assert reserve >= 1, "Can't reserve less than 1 element"

        # We will chose the largest amount of data to reserve either based on the length of data list itself, or the reserve amount

        data_len = len(data)
        to_reserve = data_len if data_len > reserve else reserve
        if to_reserve != 1:
            # This formula ensures that we always reserve power-of-2 elements, even if we request a slightly different number.
            # Instead of 7 -  we will reserve 8, and instead of 1000, we will reserve 1024
            to_reserve = int(2**np.ceil(np.log2(reserve)))

        self.array = np.empty(to_reserve, dtype=dtype)
        self.length = 0

        # Of course, if there is any data
        if data_len > 0:
            self.append(data)

    def capacity(self) -> int:
        "The amount of data that this list has reserved for future operations"
        return len(self.array)
    
    def __len__(self) -> int:
        return self.length
    
    def _resize(self, need: int):
        """
        Resize this array (double itx capacity) to accomodate the required `need` amount of values.
        It will automatically increase the array's capacity and move the original data to it.
        """

        # This can be done better using logarithms, but I did it the dumb way
        capacity = len(self.array)
        while capacity < need:
            capacity *= 2

        data = self.array
        self.array = np.empty(capacity, self.dtype())
        self.array[:len(data)] = data

    def _ensure_can_fit(self, amount: int):
        "Simply check if this list has enough capacity to fit the provided amount of elements, and if not - resize itself to fit more"
        if self.capacity()-self.length < amount:
            self._resize(self.length+amount)

    def is_empty(self) -> bool:
        return self.length == 0
    
    def dtype(self) -> np.dtype:
        "Get the dataype of this array"
        return self.array.dtype

    def push(self, element: Any):
        "Add a single element at the end of the array"
        self._ensure_can_fit(1)
        self.array[self.length] = element
        self.length += 1

    def append(self, elements: Union[np.ndarray, list]):
        "Append a list of values or a numpy array. For numpy arrays, make sure to "

        if type(elements) == np.ndarray:
            assert elements.dtype == self.array.dtype, "Type mistmatch when adding numpy arrays"

        elements_len = len(elements)
        assert elements_len > 0, "Can't append an empty numpy array"
        
        self._ensure_can_fit(elements_len)
        
        self.array[self.length:self.length+elements_len] = elements
        self.length += elements_len

    def pop(self) -> Any:
        "Remove the last element from the array"

        if self.length == 0:
            raise IndexError("Can't pop an empty Numpy List")
        
        self.length -= 1
        return self.array[self.length]
    
    def get_array(self) -> np.ndarray:
        "Get the internal numpy array slice of this list"
        return self.array[:self.length]
    
    def __getitem__(self, index: int) -> Any:
        return self.array[:self.length][index]

    def __setitem__(self, index: int, value: Any):
        self.array[:self.length][index] = value
    
    def clear(self):
        "Reset the length of the array to zero. This doesn't affect the capacity however"
        self.length = 0