from resources import Resources
from ward import test

@test("Test resources initialisation")
def _():
    s = Resources(5, 5.0, "hello")

    assert s[int] == 5
    assert s[float] == 5.0
    assert s[str] == "hello"

    # We're using get here since the entry doesn't exist because accessing it via __getitem__ will throw an error
    assert s.get(list) is None

@test("Test resources removal")
def _():
    s = Resources()

    assert s.get(int) is None
    
    s.insert(35)
    s.insert(12.04)

    assert s.get(int) == 35

    assert s.remove(int) == 35

    assert s.get(int) is None