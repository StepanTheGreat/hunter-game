"Session related code - Server, Client, shared stuff and so on"

from plugin import Plugin, Resources

from plugins.network import *

from .client import ClientPlugin, CLIENT_ONLY_RPCS, CLIENT_HOST_RPCS
from .listener import LISTENER_RPCS, LISTENER_PORT
from .server import ServerPlugin
from .server.session import ServerSession
from .server.rpcs import SERVER_RPCS

from .components import SessionComponentPlugin, NetworkEntityMap

def create_host_session(resources: Resources):
    """
    Create a host session (both the client and the server). While it is true that the connection
    in this case will be immediate - still, try to treat it the same way as `try_create_client_session`,
    as this will unify the logic better.
    """

    close_sessions(resources)

    client = Client(resources)
    client.attach_rpcs(*CLIENT_HOST_RPCS)

    server = Server(resources, 5)
    server.attach_rpcs(*SERVER_RPCS)
    session = ServerSession(client.get_addr())

    print("Client address:", client.get_addr())
    print("Server address:", server.get_addr())

    client.try_connect(server.get_addr())

    for res in (client, server, session):
        resources.insert(res)

def try_create_client_session(resources: Resources, to: tuple[str, int]):
    """
    Try create a client session by connecting to the provided server. This operation
    doesn't return immediately, and instead will only push events like `ServerConnectedEvent` or
    `ServerConnectionFailEvent`.

    In those cases the `Client` resource will be removed automatically.
    """
    close_sessions(resources)

    client = Client(resources)
    client.attach_rpcs(*CLIENT_ONLY_RPCS)
    client.try_connect(to)

    resources.insert(client)

def close_sessions(resources: Resources):
    "Close all network sessions, be it from a client, server or so on - will clean everything"

    # This is a highly important step, as it ensures stability when relaunching sessions
    resources[NetworkEntityMap].reset()

    if Client in resources:
        resources[Client].close()

    if Server in resources:
        resources[Server].close()
    
    for res in (Client, Server, ServerSession):
        resources.remove(res)

def attach_listener(resources: Resources):
    detach_listener(resources)

    listener = Listener(resources, LISTENER_PORT)
    listener.attach_rpcs(*LISTENER_RPCS)

    resources.insert(listener)

def detach_listener(resources: Resources):
    if Listener in resources:
        resources[Listener].close()
        resources.remove(Listener)

def on_server_disconnected(resources: Resources, _):
    """
    Fired either when the client has failed to connect to the server, or when it was disconnected. 
    In both of these cases it's simply going to cleanup all available session-related resources.
    """
    close_sessions(resources)

class SessionPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            ClientPlugin(),
            ServerPlugin(),
            SessionComponentPlugin()
        )

        app.add_event_listener(ServerDisonnectedEvent, on_server_disconnected)
        app.add_event_listener(ServerConnectionFailEvent, on_server_disconnected)