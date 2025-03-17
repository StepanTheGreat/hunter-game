import json
import typing
import dataclasses

class TypedDataclassTypeMismatch(Exception):
    "An exception that gets raised when a type mismatch occurs between the constructed typed dataclass and its class definition"

C = typing.TypeVar("C")

def __get_type_mismatches(cls: object) -> dict:
    mismatch_dict = {}
    for attr_name, attr_def in cls.__dataclass_fields__.items():
        expected_type = attr_def.type
        got_type = type(getattr(cls, attr_name))
        if not (got_type is expected_type):
            mismatch_dict[attr_name] = (expected_type, got_type)
    return mismatch_dict

def __typed_post_init(cls: any):
    ty_mismatches = __get_type_mismatches(cls)
    if len(ty_mismatches) > 0:
        class_name = type(cls).__name__
        # This is confusing code, but we're constructing here an error message that is understandable to read
        details = "\n    ".join(f'In field "{attr}" expected type {expected.__name__}, got {got.__name__}' for attr, (expected, got) in ty_mismatches.items())
        raise TypedDataclassTypeMismatch(f"Got a type mismatch when constructing {class_name}:\n    {details}")

def typed_dataclass(cls: object) -> object:
    """
    Basically a `dataclass` from `dataclasses`, but with additional post processing for strict types.
    This is especially important when deserializing JSON objects.
    """
    cls.__post_init__ = __typed_post_init
    cls.__is_typed_dataclass = True
    cls = dataclasses.dataclass(cls)
    return cls

def load_config(dclass: C, json_s: str) -> C:
    "Load a config from a json string. The class in the first argument has to be a dataclass"

    assert dclass.__dict__.get("__is_typed_dataclass"), "Only typed dataclasses can be loaded from JSON"

    loaded = json.loads(json_s)
    
    return dclass(**loaded)

def load_config_file(dclass: C, json_path: str) -> C:
    "The same as `load_config`, but for directly loading from the file system"

    assert dclass.__dict__.get("__is_typed_dataclass"), "Only typed dataclasses can be loaded from JSON"

    with open(json_path, "rb") as file:
        loaded = json.load(file)

    return dclass(**loaded)    