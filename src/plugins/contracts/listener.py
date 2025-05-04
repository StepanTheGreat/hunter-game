from plugins.shared.network import rpc

@rpc("b")
def notify_available_server(resources: Resources, can_accept: int):
    ip, port = get_rpc_caller_addr()

    print(f"Server found at {ip}:{port} with {MAX_PLAYERS-can_accept}/{MAX_PLAYERS} players.")


LISTENER_RPCS = (
    notify_available_server,
)
"The RPCs used by listeners. Not a huge amount honestly"