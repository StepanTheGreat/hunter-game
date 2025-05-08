"""
Some common abstractions for networking
"""

from typing import Callable, Union

from plugin import Resources, Plugin, Schedule, event, EventWriter
from itertools import count
import struct

<<<<<<< HEAD
from modules.time import Clock

from modules.network import HighUDPClient, HighUDPServer, BroadcastListener, get_current_addr
=======
from core.time import Clock

from modules.network import HighUDPClient, HighUDPServer, BroadcastReceiver, BroadcastSender, get_current_ip
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75

MAX_RPC_FUNC = 256
DEFAULT_RPC_RELIABILITY = False
"By default, all RPCs are unreliable, unless explicitly changed"

ENDIAN = "!"
"Standardized endian value used for all RPC's"

_rpc_id_counter = count(0, step=1)
_rpc_caller_addr: tuple[str, int] = None

def get_rpc_caller_addr() -> tuple[str, int]:
    """
    Get the current RPC caller's IP address. This function can only be called inside RPC functions,
    in any other case it will throw an error.
    """

    assert _rpc_caller_addr is not None, "Can't get RPC caller's address outside an RPC function"
    return _rpc_caller_addr

def _set_rpc_caller_addr(to: Union[tuple[str, int], None]):
    global _rpc_caller_addr
    _rpc_caller_addr = to

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

def _parse_rpc_call(call: bytes) -> Union[tuple[int, bytes], None]:
    return call[0], call[1:] if len(call) > 0 else None

def _try_call_rpc(
    rpcs: dict[int, Callable], 
    resources: Resources, 
    caller_addr: tuple[str, int],
    rpc_call: bytes,
):
    """
    This functions will try to parse an RPC call, and if it's valid, and is registered in the database - 
    try call the RPC.
    This function still can crash, since an RPC can throw an `RPCFormatError` due to wrong format, so
    it's important to also catch this error outside.
    """
    rpc_call = _parse_rpc_call(rpc_call)
    if rpc_call is None:
        return
    
    rpc_id, rpc_args = rpc_call
    if rpc_id not in rpcs:
        return
    
    _set_rpc_caller_addr(caller_addr) # It's important we set the caller's address before calling it

    try:
        rpcs[rpc_id](resources, rpc_args)
    except RPCFormatError:
        # In the future this should be present on every single actor separately
        print("Malformed input used on RPC {}", rpc_id)

    _set_rpc_caller_addr(None)

def _attach_rpcs(to: dict[int, Callable], rpcs: tuple[Callable, ...]):
    for rpc in rpcs:
        assert is_rpc(rpc), "Only systems with @rpc or @rpc_raw decorators can be attached"
        assert rpc.__rpc_id not in to, "The RPC under the same ID is already attached"
        to[rpc.__rpc_id] = rpc

class Client:
    "A client abstractions for managing game clients"

    # We'll do 5 seconds in total
    CONNECTION_ATTEMPTS = 10
    CONNECTION_ATTEMPT_DELAY = 0.5

    def __init__(self, resources: Resources, rpcs: tuple[Callable, ...] = ()):
        self.resources = resources
        self.ewriter = resources[EventWriter]
<<<<<<< HEAD
        self.client = HighUDPClient((get_current_addr(), 0))
=======
        self.client = HighUDPClient((get_current_ip(), 0))
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
        self.rpcs: dict[int, Callable] = {}

        self._init_hooks()
        self.attach_rpcs(*rpcs)

    def _init_hooks(self):
        def on_client_connection():
            self.ewriter.push_event(ServerConnectedEvent())
        
        def on_client_disconnection():
            self.ewriter.push_event(ServerDisonnectedEvent())

        def on_client_connection_fail():
            self.ewriter.push_event(ServerConnectionFailEvent())

        self.client.on_connection = on_client_connection
        self.client.on_disconnection = on_client_disconnection
        self.client.on_connection_fail = on_client_connection_fail

    def get_addr(self) -> tuple[str, int]:
        return self.client.get_addr()
    
    def is_connected(self) -> bool:
        return self.client.is_connected()

    def try_connect(self, to: tuple[str, int]):
        """
        Kickstart client's attemp to connect. This operation can fail, so make sure to listen for
        connection failure events.

        Furthermore, if the client is already connected - this method will panic. 
        """

        assert not self.client.is_connected()

        self.client.connect(to, Client.CONNECTION_ATTEMPTS, Client.CONNECTION_ATTEMPT_DELAY)

    def attach_rpcs(self, *rpcs: Callable):
        _attach_rpcs(self.rpcs, rpcs)

    def tick(self, dt: float):
        self.client.tick(dt)
        addr = self.client.get_server_addr()
        while self.client.has_packets():
            data = self.client.recv()
            _try_call_rpc(self.rpcs, self.resources, addr, data)

    def call(self, rpc_func: Callable, *args):
        "Call the provided RPC function with the provided arguments on the server (if it's attached there)"
        self.client.send(
            serialize_call(rpc_func, args), 
            is_rpc_reliable(rpc_func)
        )

    def close(self):
        "Always close the client when you're done with it"
        self.client.close()

class Server:
    def __init__(self, resources: Resources, max_clients: int, rpcs: tuple[Callable, ...] = ()):
        self.resources = resources
        self.ewriter = resources[EventWriter]
<<<<<<< HEAD
        self.server = HighUDPServer((get_current_addr(), 0), max_clients)
=======
        self.server = HighUDPServer((get_current_ip(), 0), max_clients)
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
        self.rpcs: dict[int, Callable] = {}

        self._init_event_hooks()
        self.attach_rpcs(*rpcs)

    def _init_event_hooks(self):
        def on_server_connection(addr: tuple[str, int]):
            self.ewriter.push_event(ClientConnectedEvent(addr))
        
        def on_server_disconnection(addr: tuple[str, int]):
            self.ewriter.push_event(ClientDisconnectedEvent(addr))

        self.server.on_connection = on_server_connection
        self.server.on_disconnection = on_server_disconnection

<<<<<<< HEAD
=======
    def accept_incoming_connections(self, to: bool):
        "Change whether the server can accept new incoming connections or not"

        self.server.accept_incoming_connections(to)

>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
    def get_addr(self) -> tuple[str, int]:
        return self.server.get_addr()
    
    def attach_rpcs(self, *rpcs: Callable):
        _attach_rpcs(self.rpcs, rpcs)

    def tick(self, dt: float):
        self.server.tick(dt)
        while self.server.has_packets():
            data, addr = self.server.recv()
            _try_call_rpc(self.rpcs, self.resources, addr, data)

    def call(self, addr: tuple[str, int], rpc_func: Callable, *args):
        "Call the provided RPC function with the provided arguments on the provided client (if it's attached there)"
        self.server.send_to(
            addr,
            serialize_call(rpc_func, args), 
            is_rpc_reliable(rpc_func)
        )

    def call_all(self, rpc_func: Callable, *args):
        "Execute the RPC function on all connected clients"
        rpc_call = serialize_call(rpc_func, args)
        reliability = is_rpc_reliable(rpc_func)

        for addr in self.server.get_connection_addresses():
            self.server.send_to(addr, rpc_call, reliability)

    def close(self):
        "Always close the server when you're done with it"
        self.server.close()

class BroadcastWriter:
    def __init__(self):
        self.writer = BroadcastSender(get_current_ip())

    def broadcast_call(self, port: int, rpc_func: Callable, *args):
        """
        Broadcast the RPC function on the provided port. 
        
        An additional important fact is that all broadcast RPC calls are unreliable, as there's
        no connection established. So, it's not possible to use reliable features when broadcasting.
        """

        self.writer.broadcast(
            port,
            serialize_call(rpc_func, args), 
        )

    def close(self):
        "Always close the writer when you're done with it"

<<<<<<< HEAD
class Listener:
    def __init__(self, resources: Resources, port: int, rpcs: tuple[Callable, ...] = ()):
        self.resources = resources
        self.listener = BroadcastListener(("0.0.0.0", port))
=======
        self.writer.close()

class BroadcastListener:
    def __init__(self, resources: Resources, port: int, rpcs: tuple[Callable, ...] = ()):
        self.resources = resources
        self.listener = BroadcastReceiver(("0.0.0.0", port))
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
        self.rpcs: dict[int, Callable] = {}

        self.attach_rpcs(*rpcs)

    def attach_rpcs(self, *rpcs: Callable):
        _attach_rpcs(self.rpcs, rpcs)

    def tick(self, _dt: float):
        self.listener.fetch()
        while self.listener.has_packets():
            data, addr = self.listener.recv()
            _try_call_rpc(self.rpcs, self.resources, addr, data)

    def close(self):
        "Always close the listener when you're done with it"
        self.listener.close()

<<<<<<< HEAD
def clean_network_actors(resources: Resources, *actors: type):
    """
    A general purpose function for cleaning up network actors (Server/Client/Listener).
=======
def clean_network_actors(resources: Resources, *actors: Union[Server, Client, BroadcastListener, BroadcastWriter]):
    """
    A general purpose function for cleaning up network actors (Server/Client/BroadcastListener).
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
    Not to be confused with the system of similar name - it's a system, and it will get called
    immediately when the app closes.
    """

<<<<<<< HEAD
    for actor in actors:
        actor = resources.remove(actor)
=======
    for actor_ty in actors:
        actor = resources.remove(actor_ty)
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
        if actor is not None:
            actor.close()

def update_network_actors(resources: Resources):
    dt = resources[Clock].get_fixed_delta()

    # The order here is specific: first update the client, so that they can send a message
    # Then, the server should receive this message, and notify both the client and the listener
    # Finally, the listener can act on server's action.
    # On the next tick the Client would be able to receive Server's message
    for actor_ty in (Client, Server, BroadcastListener):
        actor = resources.get(actor_ty)
        if actor is not None:
            actor.tick(dt)

<<<<<<< HEAD
def insert_network_actor(resources: Resources, actor: Union[Server, Client, Listener]):
=======
def insert_network_actor(resources: Resources, actor: Union[Server, Client, BroadcastListener, BroadcastWriter]):
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
    """
    Insert a network actor resource, and if it's present - close the existing one. 
    Please prefer using this function over simply inserting network actors directly, 
    as overwriting existing network actors without closing them will lead to unclosed sockets.
    """

    actor_ty = type(actor)

<<<<<<< HEAD
    if actor_ty in resources:
        resources.remove(actor_ty).close()
=======
    clean_network_actors(resources, actor_ty)
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75

    resources.insert(actor)

def cleanup_network_actors(resources: Resources):
    "Clean all network actors when the app gets closed."

<<<<<<< HEAD
    clean_network_actors(resources, Listener, Client, Server)
=======
    clean_network_actors(resources, BroadcastWriter, BroadcastListener, Client, Server)
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75

@event
class ClientConnectedEvent:
    "A client has connected to the server. It's fired on the host (i.e. when you're the server)"
    def __init__(self, addr: tuple[str, int]):
        self.addr = addr

@event
class ClientDisconnectedEvent:
    "A client has disconnected from the server. It's fired on the host (i.e. when you're the server)"
    def __init__(self, addr: tuple[str, int]):
        self.addr = addr

@event
class ServerConnectedEvent:
    "A connection to the server was succesfully established (i.e. when you're the client)"

@event
class ServerDisonnectedEvent:
    "Connection was lost with the server (or forcefully disconnected) (i.e. when you're the client)"

@event
class ServerConnectionFailEvent:
    "A connection to the server was unsuccesful (i.e. when you're the client)"

class NetworkPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.FixedUpdate, update_network_actors)
        app.add_systems(Schedule.Finalize, cleanup_network_actors)