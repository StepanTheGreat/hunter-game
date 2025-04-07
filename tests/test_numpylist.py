from ward import test, raises

import numpy as np
from modules.numpylist import NumpyList

@test("Test the initial capacity and size")
def _():

    # An empty numpy list should have zero length but 1 reserved element
    l = NumpyList()
    assert len(l) == 0
    assert l.capacity() == 1

    # An empty list with 8 reserved elements
    l = NumpyList(reserve=8)
    assert len(l) == 0
    assert l.capacity() == 8

    # If we initialize a list with data - it should have the length of said data, + additional capacity
    l = NumpyList([1, 2, 3])
    assert len(l) == 3
    assert l.capacity() == 4

    # If our capacity is less than the initial data - our numpy list should reserve its array for the initial list instead
    l = NumpyList([1, 2, 3], reserve=2)
    assert len(l) == 3
    assert l.capacity() == 4

    # But if it's the other way around - it should prefer the reserve variable
    l = NumpyList([1, 2, 3], reserve=12)
    assert len(l) == 3
    assert l.capacity() == 16

@test("Test reallocations")
def _():
    # In this test we will make sure that the capacity and the amount of reallocations grows logarithmically
    l = NumpyList([])

    capacity = l.capacity()
    reallocations = 0
    for i in range(48):
        l.push(i)

        new_capacity = l.capacity()
        if new_capacity > capacity:
            capacity = new_capacity
            reallocations += 1

    assert reallocations == 6
    assert len(l) == 48
    assert l.capacity() == 64
    assert (l.get_array() == range(48)).all()

@test("Test element reservation")
def _():
    # In this test we will make sure that the capacity and the amount of reallocations grows logarithmically
    l = NumpyList(reserve=100)

    assert len(l) == 0
    assert l.capacity() == 128

@test("Test if elements are intact when the array gets reallocated")
def _():
    l = NumpyList([])

    l.append([1, 2, 3, 4, 5, 6])
    
    assert l[0] == 1
    assert l[5] == 6
    assert l[-1] == 6

    # Force the array to reallocate
    l.append([7, 8, 9])

    assert l[0] == 1
    assert l[5] == 6
    assert l[-1] == 9

@test("Test list's type")
def _():
    l = NumpyList()

    l.append([1, 2, 3, 4, 5, 6])
    assert l.dtype() == np.float64

    l = NumpyList(dtype=np.uint32)

    # Should pass
    l.append([1, 2, 3, 4, 5, 6])

    # Should throw an error, since datatypes do not match
    with raises(AssertionError):
        l.append(np.array([1.0, 1.5]))


