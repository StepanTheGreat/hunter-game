from plugin import Resources
from ward import test

@test("Test resources initialisation")
def _():
    r = Resources(5, 5.0, "hello")

    assert r[int] == 5
    assert r[float] == 5.0
    assert r[str] == "hello"

    # We're using get here since the entry doesn't exist because accessing it via __getitem__ will throw an error
    assert r.get(list) is None

@test("Test resources removal")
def _():
    r = Resources()

    assert r.get(int) is None
    
    r.insert(35)
    r.insert(12.04)

    assert r.get(int) == 35

    assert r.remove(int) == 35

    assert r.get(int) is None