from plugin import Resources

from plugins.shared.network import rpc, get_rpc_caller_addr

LISTENER_PORT = 1567

@rpc("4BH2B")
def notify_available_server_rpc(
    resources: Resources, 
    ip_a: int, ip_b: int, ip_c: int, ip_d: int, 
    port: int,
    max_players: int, 
    players: int
):
    ip, port = f"{ip_a}.{ip_b}.{ip_c}.{ip_d}", port

    print(f"Server found at {ip}:{port} with {players}/{max_players} players.")


LISTENER_RPCS = (
    notify_available_server_rpc,
)
"The RPCs used by listeners. Not a huge amount honestly"