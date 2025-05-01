from plugin import Resources

from core.ecs import WorldECS

from plugins.network import rpc, rpc_raw, only_client, get_rpc_caller_addr
from plugins.components import Position, Velocity

from ..components import NetEntity
from . import ServerSession

@rpc("2hB?")
def control_player(
    resources: Resources, 
    pos_x: int, pos_y: int, 
    vel_angle: int, vel_length: bool
):
    session = resources[ServerSession]
    player_addr = get_rpc_caller_addr()
    print("Received a request to move from player", player_addr)


SERVER_RPCS = (
    control_player,
)