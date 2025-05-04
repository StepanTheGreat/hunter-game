from plugin import Resources

from plugins.shared.network import rpc, get_rpc_caller_addr

LISTENER_PORT = 1567

@rpc("BB")
def notify_available_server_rpc(resources: Resources, max_players: int, players: int):
    ip, port = get_rpc_caller_addr()

    print(f"Server found at {ip}:{port} with {players}/{max_players} players.")


LISTENER_RPCS = (
    notify_available_server_rpc,
)
"The RPCs used by listeners. Not a huge amount honestly"