from ward import test
from modules.inteprolation import Interpolated, InterpolatedDegrees

import numpy as np

@test("Test interpolation")
def _():
    i = Interpolated(0)
    i.push_value(100)

    # We have 2 values: 0 and 100, so 0.5 of should be equal to 50 
    assert i.get_interpolated(0.5) == 50
    assert i.get_value() == 100

    i.push_value(60)

    # Pushing another 50, we will now have 60

    assert i.get_interpolated(0.75) == 100+(60-100)*0.75
    assert i.get_value() == 60

@test("Test angle interpolation")
def _():
    rad = lambda degrees: np.radians(degrees)-np.pi

    i = InterpolatedDegrees(rad(350))

    i.push_value(rad(10))

    # The point of this test is that the interpolation from 350 should chose the shorted path to 10
    # In normal inteprolation it would mean going backwards from 350, to the left, to 10.
    # But our desired behaviour is to actually wrap around, to the right, and then hit 10
    assert i.get_interpolated(0) == rad(350)
    assert i.get_interpolated(0.25) == rad(355)
    assert i.get_interpolated(0.5) == rad(360)
    assert i.get_interpolated(0.75) == rad(5)
    assert i.get_interpolated(1) == rad(10)

    # We're doing the same thing, but in the opposite direction
    i.push_value(rad(350))
    assert i.get_interpolated(0) == rad(10)
    assert i.get_interpolated(0.25) == rad(5)
    assert i.get_interpolated(0.5) == rad(0)
    assert i.get_interpolated(0.75) == rad(355)
    assert i.get_interpolated(1) == rad(350)