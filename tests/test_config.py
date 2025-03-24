import modules.config as config
import dataclasses
from ward import test, raises

@test("Test proper config loading")
def _():
    @config.typed_dataclass
    class MyConf:
        number: int
        name: str
        default: int = 30
        planet: str = "Mars"

    json_s = '''{
        "number": 5,
        "name": "Mark?",
        "planet": "Jupiter"
    }'''

    loaded = config.load_config(MyConf, json_s)

    assert loaded.number == 5
    assert loaded.default == 30
    assert loaded.name == "Mark?"
    assert loaded.planet == "Jupiter"

@test("Raise an exception when config types mismatch")
def _():
    @config.typed_dataclass
    class MyConf:
        number: int
        name: str
        default: int = 30
        planet: str = "Mars"

    json_s = '''{
        "number": "one",
        "name": "Mark?",
        "default": null
    }'''

    with raises(config.TypedDataclassTypeMismatch):
        config.load_config(MyConf, json_s)

@test("Panic when an object that is not a typed dataclass is loaded from JSON")
def _():
    @dataclasses.dataclass
    class MyConf:
        number: int
        name: str
        default: int = 30
        planet: str = "Mars"

    json_s = '''{
        "number": "one",
        "name": "Mark?",
        "default": null
    }'''

    with raises(AssertionError):
        config.load_config(MyConf, json_s)

@test("Throw an error when default type and value's type mismatch")
def _():
    @config.typed_dataclass
    class MyConf:
        number: int
        name: str
        default: int = None
        planet: str = "Mars"

    with raises(config.TypedDataclassTypeMismatch):
        MyConf(number=5, name="name")

@test("Throw an error when a required attribute isn't declared")
def _():
    @config.typed_dataclass
    class MyConf:
        number: int
        name: str
        default: int = None
        planet: str = "Mars"

    with raises(TypeError):
        MyConf(name="name")