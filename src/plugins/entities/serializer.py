"""
This module defines entity serialization - an ability to serialize any entity to a stream of
bytes, send it across the network, and then deserialize into its own proper entity.

This allows for highly scalable code, as defining a new serialized enitity is only a matter of
additional class and its proper bytes parsing logic.
On the client/server side, when proper entity serializer is created - any entity can be constructed
just by passing its ID and proper amount of arguments.
"""

from typing import Any, Optional, Callable
import struct

from itertools import count

SERIALIZER_LIMIT = 256

_serializer_map: dict[int, type] = {}
_serializer_id = count(0)

def _get_next_serializer_id() -> int:
    new_id = next(_serializer_id)

    assert new_id < SERIALIZER_LIMIT, f"Reached the serializer limit of {SERIALIZER_LIMIT}"

    return new_id

def auto_deser(byte_format: str):
    """
    A decorator that can be applied to your function to automatically deserialize the provided
    byte format into arguments. This can save a lot of time, especially since most entities can be
    constructed individually using constant-sized byte sized (no dynamic data).
    One additional benefit is that it constructs a reusable `Struct` object, so it will be a bit
    faster for frequent parsing (not guaranteed).

    An example:
    ```
    class MyCustomDeserializer:
        ...

        @auto_deser("c?b")
        def deserialize(c: str, b: bool, num: int) -> Optional[Any]:
            "Your custom logic here"
    ```

    ## Notes
    1. If this fails to parse bytes properly - it will just going to automatically return `None`, without
    executing your function.
    2. Do not define the endian, as it's automatically defined as the network endian `!`
    """

    struct_format = struct.Struct("!"+byte_format)
    def decorator(func: Callable):
        def wrapper(bytes: bytes) -> Optional[Any]:
            try:
                args = struct_format.unpack(bytes)
                return func(*args)
            except struct.error:
                return None
            
        return wrapper
    
    return decorator

class EntitySerializer:

    def serialize(components: dict[type, Any]) -> bytes:
        """
        Your custom serialization logic. Please, don't serialize components like 
        EntityUID, as they're serialized and added automatically. The same goes for the internal
        ID of this serializer! Only serialize 
        """

    def deserialize(data: bytes) -> Optional[tuple]:
        """
        Your custom deserialization logic. Please, don't try to sereliaze the `NetEntity`
        component, as it will be added by default at the end. Only return components that 
        are neccessary for your entity.
        """

def get_serializer_id(cls: type) -> int:
    assert hasattr(cls, "__serializer_id"), "The provided type isn't a serializer"

    return cls.__serializer_id

def get_serializer_by_id(uid: int) -> Optional["EntitySerializer"]:
    "Try get a deserializer under provided ID"
    return _serializer_map.get(uid)

def entity_serializer(cls: EntitySerializer):
    """
    A decorator for defining and registering entity serializers. When you define a new entity
    serializer - you must always register it using this decorator, as this will provide it
    a unique ID that can be used across the network and it will get registered in the local
    database.
    """
    serializer_id = _get_next_serializer_id()

    _serializer_map[serializer_id] = cls
    cls.__serializer_id = serializer_id

    return cls