"""
Some common abstractions for networking
"""

from typing import Callable, Union

from itertools import count
import struct

from modules.network import HighUDPClient, HighUDPServer

MAX_RPC_FUNC = 256

ENDIAN = "!"
"Standardized endian value used for all RPC's"

__rpc_database: dict[int, Callable] = {}
__rpc_id_counter = count(0, step=1)

class RPCFormatError(Exception):
    "The arguments passed to the RPC were malformed, thus the RPC wasn't executed."

def __register_rpc(rpc_func: Callable, serialize_call: Callable):
    """
    Registers an RPC function into the database and attaches some internal attributes
    like its internal RPC ID and its `serialize_call` method. 
    """
    new_rpc_id = next(__rpc_id_counter)
    assert new_rpc_id < MAX_RPC_FUNC, f"Reached the maximum amount of RPC functions: {MAX_RPC_FUNC}"

    __rpc_database[new_rpc_id] = rpc_func

    # We'll assign this function its unique ID as well, so it can be retrieved by other APIs
    rpc_func.__rpc_id = new_rpc_id

    # We'll assign its helper `serialize_call` method 
    rpc_func.serialize_call = serialize_call

def rpc(struct_format: str):
    """
    A function decorator that essentially transforms a function into a function that will only 
    accept arguments in the form of a byte array. What this essentially allows us to do, is to make it possible
    to execute the function throughh network, without passing Python values. 

    This RPC additionally will register itself into its internal session-global database, so it can be used easily
    in conjunction with Server/Client classes.

    It takes 1 argument: the `byte_format` in which it will try to parse the input and convert it into
    python arguments ([you can read about it here](https://docs.python.org/3/library/struct.html)).
    
    ## Note:
    1. This decorator will automatically use the big-endian for your format (it's added automatically), so don't
    add it to your byte formats.
    2. Since Python's `struct` module when unpacking returns a tuple - this decorator will automatically unpack
    all arguments in your function. No need to do that:
    ```
    @rpc("ii")
    def my_rpc(args: tuple):
        # Don't do this
        ...

    @rpc("ii")
    def my_rpc(a: int, b: int):
        # Do this instead
        ...
    ```
    3. To make it a bit simpler to work with the RPC callbacks - this function has a simple method called `serialize_call`,
    which takes an unspecified amount of arguments and tries to pack them into bytes, according to the RPC function's
    byte format. You don't need to tinker with bytes, you can just do this instead:
    ```
    @rpc("ii")
    def my_rpc(a: int, b: int):
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
        def rpc_func(serialized_arguments: bytes):
            try:
                parsed_args = format_struct.unpack(serialized_arguments)
                func(*parsed_args)
            except struct.error:
                raise RPCFormatError()

        def serialize_call(*args) -> bytes:
            "Serialize provided arguments into bytes that can be used to call the RPC function"
            return format_struct.pack(*args)

        __register_rpc(rpc_func, serialize_call)

        return rpc_func
    return decorator

def rpc_raw(func):
    """
    Before you use this RPC decorator, you should first read about the `rpc`.
    This decorator solely exists for edge cases, like managing growable structures in RPC's. If you have a consistent
    RPC structure and don't expect any growable data (or you do, but wasting a bit memory is acceptable) - use `@rpc`,
    as it will handle most stuff for you.

    In any other case, this RPC will simply throw you bytes, which you will analyze yourself. If you do encounter a
    parsing error - you could throw the `RPCFormatError` exception in your function, to help the APIs catch and act
    on suspicious behaviour.
    """

    # We can't avoid this method due to common API
    def serialize_call(args: bytes) -> bytes:
        return args
    
    __register_rpc(func, serialize_call)
    return func

# TODO: Currently it's unclear how to pass caller's IP address into RPC calls without resorting to global
# TODO: state. Perhaps indeed, Godot's approach could be used, where one can get the current callee's IP address
# TODO: using a special function like `get_rpc_caller_ip`, which should be manually set by external APIs before 
# TODO: executing RPC functions.
# TODO: When used outside - it should throw an exception.

class Client:
    def __init__(self, addr: tuple[str, int]):
        self.client = HighUDPClient(addr)

class Server:
    def __init__(self, addr: tuple[str, int], max_clients: int):
        self.server = HighUDPServer(addr, max_clients)