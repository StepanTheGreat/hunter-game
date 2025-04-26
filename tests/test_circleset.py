from ward import test
from modules.circleset import CircleSet

@test("Circular set should rotate")
def _():
    # Create a set with size of 10
    s = CircleSet(10)

    # Now, we'll add 11 elements to this set.
    # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
    # And.... it should rotate itself
    # 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
    for i in range(10+1):
        s.add(i)

    # 0 shouldn't be there
    assert 0 not in s
    # But 1 should
    assert 1 in s

    # Let's re-add this 0
    # 2, 3, 4, 5, 6, 7, 8, 9, 10, 0
    s.add(0)

    # Now 1 should be absent!
    assert 1 not in s

    # The set should be at its full capacity
    assert len(s) == 10