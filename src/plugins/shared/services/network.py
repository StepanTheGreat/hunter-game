"""
Some common abstractions for networking
"""

from plugin import Resources, Plugin, Schedule, EventWriter

from plugins.shared.events.network import *

from core.time import Clock

from modules.network import *
from modules.rpc import *

from typing import Callable, Union, Optional

class RPCCallerAddress:
    """
    The global RPC caller's address that changes depending on who's calling the RPC.
    It's important to note that this resource can only be used inside RPC contexts, and in any
    other case getting the address will raise an exception.
    """

    def __init__(self):
        self.addr: Optional[tuple[str, int]] = None

    def get_addr(self) -> tuple[str, int]:
        "Get the current RPC caller's address. If called outside RPC functions - will raise an exception"

        assert self.addr is not None, "Can't get RPC caller's address outside RPC contexts"

        return self.addr
    
    def _set_addr(self, to: Optional[tuple[str, int]]):
        self.addr = to

def _parse_rpc_call(call: bytes) -> Optional[tuple[int, bytes]]:
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
    rpc_caller_addr = resources[RPCCallerAddress]

    rpc_call = _parse_rpc_call(rpc_call)
    if rpc_call is None:
        return
    
    rpc_id, rpc_args = rpc_call
    if rpc_id not in rpcs:
        return
    
    rpc_caller_addr._set_addr(caller_addr)
    # It's important we set the caller's address before calling it

    try:
        rpcs[rpc_id](resources, rpc_args)
    except RPCFormatError:
        # In the future this should be present on every single actor separately
        print("Malformed input used on RPC {}", rpc_id)

    rpc_caller_addr._set_addr(None)

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
        self.client = HighUDPClient((get_current_ip(), 0))
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
        self.server = HighUDPServer((get_current_ip(), 0), max_clients)
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

    def accept_incoming_connections(self, to: bool):
        "Change whether the server can accept new incoming connections or not"

        self.server.accept_incoming_connections(to)

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

        self.writer.close()

class BroadcastListener:
    def __init__(self, resources: Resources, port: int, rpcs: tuple[Callable, ...] = ()):
        self.resources = resources
        self.listener = BroadcastReceiver(("0.0.0.0", port))
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

def clean_network_actors(
    resources: Resources, 
    *actors: Union[Server, Client, BroadcastListener, BroadcastWriter]
):
    """
    A general purpose function for cleaning up network actors (Server/Client/BroadcastListener).
    Not to be confused with the system of similar name - it's a system, and it will get called
    immediately when the app closes.
    """

    for actor_ty in actors:
        actor = resources.remove(actor_ty)
        if actor is not None:
            actor.close()

def insert_network_actor(
    resources: Resources, 
    actor: Union[Server, Client, BroadcastListener, BroadcastWriter]
):
    """
    Insert a network actor resource, and if it's present - close the existing one. 
    Please prefer using this function over simply inserting network actors directly, 
    as overwriting existing network actors without closing them will lead to unclosed sockets.
    """

    actor_ty = type(actor)

    clean_network_actors(resources, actor_ty)

    resources.insert(actor)


def update_network_actors_systems(resources: Resources):
    dt = resources[Clock].get_fixed_delta()

    # The order here is specific: first update the client, so that they can send a message
    # Then, the server should receive this message, and notify both the client and the listener
    # Finally, the listener can act on server's action.
    # On the next tick the Client would be able to receive Server's message
    for actor_ty in (Client, Server, BroadcastListener):
        actor = resources.get(actor_ty)
        if actor is not None:
            actor.tick(dt)

def on_final_cleanup_network_actors(resources: Resources):
    "Clean all network actors when the app gets closed."

    clean_network_actors(resources, BroadcastWriter, BroadcastListener, Client, Server)

class NetworkPlugin(Plugin):
    def build(self, app):
        app.insert_resource(RPCCallerAddress())

        app.add_systems(Schedule.FixedUpdate, update_network_actors_systems)
        app.add_systems(Schedule.Finalize, on_final_cleanup_network_actors)

# TODO: Is there a reason all this resides in this single service...? Maybe it could be
# TODO: separated into separate services on client/server?