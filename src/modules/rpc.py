from plugin import Resources

from itertools import count
import struct
from modules.network import *

from typing import Callable, Optional

MAX_RPC_FUNC = 256
DEFAULT_RPC_RELIABILITY = False
"By default, all RPCs are unreliable, unless explicitly changed"

ENDIAN = "!"
"Standardized endian value used for all RPC's"

_rpc_id_counter = count(0, step=1)

class RPCFormatError(Exception):
    "The arguments passed to the RPC were malformed, thus the RPC wasn't executed."

def _register_rpc(rpc_func: Callable, serialize_call: Callable, is_reliable: bool):
    """
    Registers an RPC function into the database and attaches some internal attributes
    like its internal RPC ID and its `serialize_call` method. 
    """
    new_rpc_id = next(_rpc_id_counter)
    assert new_rpc_id < MAX_RPC_FUNC, f"Reached the maximum amount of RPC functions: {MAX_RPC_FUNC}"

    # We'll assign this function its unique ID as well, so it can be retrieved by other APIs
    rpc_func.__rpc_id = new_rpc_id

    rpc_func.__reliable = is_reliable

    # We'll assign its helper `serialize_call` method 
    rpc_func.serialize_call = serialize_call

def rpc(struct_format: str, reliable: bool = DEFAULT_RPC_RELIABILITY):
    """
    A function decorator that essentially transforms a system into a network system that will only 
    accept arguments in a form of bytes. What this essentially allows us to do, is make it possible
    to execute the system through network, without passing Python values (well, we can't anyway). 

    Every RPC additionally gets a unique RPC identifier (1 byte integer), so it makes it extremely
    efficient to communicate between same sessions, as this decorator 

    It takes 2 argument: the `byte_format` in which it will try to parse the input and convert it into
    python arguments ([you can read about it here](https://docs.python.org/3/library/struct.html)), and
    optionally `reliable` boolean, which by default is False.
    Reliability gives an RPC function guarantees, that it's going to get delievered (even when lost).
    It does mean more latency, so this should be only done for important actions. 
    
    ## Note:
    1. This decorator will automatically use the big-endian for your format (it's added automatically), so don't
    add it to your byte formats.
    2. Since Python's `struct` module when unpacking returns a tuple - this decorator will automatically unpack
    all arguments in your function. No need to do that:
    ```
    @rpc("ii")
    def my_rpc(_, args: tuple):
        # Don't do this
        ...

    @rpc("ii")
    def my_rpc(_, a: int, b: int):
        # Do this instead
        ...
    ```
    3. To make it a bit simpler to work with the RPC callbacks - this function has a simple method called `serialize_call`,
    which takes an unspecified amount of arguments and tries to pack them into bytes, according to the RPC function's
    byte format. You don't need to tinker with bytes, you can just do this instead:
    ```
    @rpc("ii")
    def my_rpc(_, a: int, b: int):
        ...

    my_rpc(
        my_rpc.serialize_call(1, 5)
    )
    ```
    4. This RPC doesn't validate your functions in any way (for now), so make sure that the format specified
    actually matches the amount of arguments your function accepts. If not - it will painfully throw an exception
    at runtime.
    5. While Python's `struct` will convert the given data into bytes - it could still highly likely be garbage data,
    so make sure to sanitize it. Actually, sanitize everything, because you can never trust a client's input.
    """
    def decorator(func):
        format_struct = struct.Struct(ENDIAN+struct_format)
        def rpc_func(resources: Resources, serialized_arguments: bytes):
            try:
                parsed_args = format_struct.unpack(serialized_arguments)
                func(resources, *parsed_args)
            except struct.error:
                raise RPCFormatError()

        def serialize_call(*args) -> bytes:
            "Serialize provided arguments into bytes that can be used to call the RPC function"
            return format_struct.pack(*args)

        _register_rpc(rpc_func, serialize_call, reliable)

        return rpc_func
    return decorator

def rpc_raw(reliable: bool = DEFAULT_RPC_RELIABILITY):
    """
    Before you use this RPC decorator, you should first read about the `rpc`.
    This decorator solely exists for edge cases, like managing growable structures in RPC's. If you have a consistent
    RPC structure and don't expect any growable data (or you do, but wasting a bit memory is acceptable) - use `@rpc`,
    as it will handle most stuff for you.

    In any other case, this RPC will simply throw you bytes, which you will analyze yourself. If you do encounter a
    parsing error - you could throw the `RPCFormatError` exception in your function, to help the APIs catch and act
    on suspicious behaviour.
    """

    # For anyone not understanding what happens here - the python's decorator magic is as follows:
    # when a decorator is applied without parantheses: `@dec` - it calls the decorator, with its only
    # argument being the function.
    # If however, the decorator is called: `@dec()` - Python expects this decorator to return a decorator
    # function, and the arguments passed to this decorator will be passed in the decorator instead.

    # We're using `reliable` argument to make it possible to pass keyword arguments to this RPC.
    # This however, doesn't mean at all that it's going to be

    # If the first argument is a function - we're going to use the default reliability. 
    # In any other case we're using what the user gives us
    is_reliable = DEFAULT_RPC_RELIABILITY if callable(reliable) else reliable

    def decorator(func):
        # We can't avoid this method due to common API
        def serialize_call(args: bytes) -> bytes:
            return args
        
        _register_rpc(func, serialize_call, is_reliable)

        return func
    
    if callable(reliable):
        return decorator(reliable)
    else:
        return decorator

def is_rpc(rpc_func: Callable) -> bool:
    "Returns whether the provided function is an RPC function"
    return hasattr(rpc_func, "__rpc_id")

def get_rpc_id(func: Callable) -> int:
    "Get RPC's ID"
    assert is_rpc(func)

    return func.__rpc_id

def is_rpc_reliable(func: Callable) -> bool:
    "Does the RPC use reliable communication? `True` means yes"
    assert is_rpc(func)

    return func.__reliable

def serialize_call(func: Callable, args: tuple) -> bytes:
    "Constructs an entire binary RPC call, according to the RPC protocol: `[id][args][args][args]...`"
    rpc_id = get_rpc_id(func)

    return bytes([rpc_id]) + func.serialize_call(*args)