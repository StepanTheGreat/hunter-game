"The listener that listens for the server invitations and throws events"

from plugins.network import rpc, get_rpc_caller_addr

from plugin import Plugin, Resources

MAX_PLAYERS = 5
LISTENER_PORT = 1524

@rpc("b")
def notify_available_server(resources: Resources, can_accept: int):
    ip, port = get_rpc_caller_addr()

    print(f"Server found at {ip}:{port} with {MAX_PLAYERS-can_accept}/{MAX_PLAYERS} players.")


LISTENER_RPCS = (
    notify_available_server,
)
"The RPCs used by listeners. Not a huge amount honestly"