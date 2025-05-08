<<<<<<< HEAD
from plugin import Resources

from plugins.shared.network import rpc, get_rpc_caller_addr

LISTENER_PORT = 1567

@rpc("BB")
def notify_available_server_rpc(resources: Resources, max_players: int, players: int):
    ip, port = get_rpc_caller_addr()

    print(f"Server found at {ip}:{port} with {players}/{max_players} players.")
=======
from plugin import Resources, EventWriter, event

from plugins.shared.network import rpc

LISTENER_PORT = 1567

@event
class AvailableServerCommand:
    """
    Servers that haven't started the game once in a while broadcast messages of availability
    """
    def __init__(self, addr: tuple[str, int], max_players: int, players: int):
        self.addr = addr
        self.max_players = max_players
        self.players = players

@rpc("4BH2B")
def notify_available_server_rpc(
    resources: Resources, 
    ip_a: int, ip_b: int, ip_c: int, ip_d: int, 
    port: int,
    max_players: int, 
    players: int
):
    ip, port = f"{ip_a}.{ip_b}.{ip_c}.{ip_d}", port

    print(f"Found server: {ip}:{port}")

    resources[EventWriter].push_event(AvailableServerCommand((ip, port), max_players, players))
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75


LISTENER_RPCS = (
    notify_available_server_rpc,
)
"The RPCs used by listeners. Not a huge amount honestly"