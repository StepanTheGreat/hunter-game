from src.storage import Storage
from ward import test

@test("Test storage initialisation")
def _():
    s = Storage(5, 5.0, "hello")

    assert s[int] == 5
    assert s[float] == 5.0
    assert s[str] == "hello"

    # We're using get here since the entry doesn't exist because accessing it via __getitem__ will throw an error
    assert s.get(list) is None

@test("Test storage removal")
def _():
    s = Storage()

    assert s.get(int) is None
    
    s.insert(35)
    s.insert(12.04)

    assert s.get(int) == 35

    s.remove(int)

    assert s.get(int) is None