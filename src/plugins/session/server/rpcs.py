from plugin import Resources

from core.ecs import WorldECS

from plugins.network import rpc, get_rpc_caller_addr
from plugins.components import Position, Velocity

from ..pack import unpack_velocity
from .session import ServerSession

@rpc("2hB?")
def control_player(
    resources: Resources, 
    pos_x: int, pos_y: int, 
    vel_angle: int, vel_length: bool
):
    session = resources[ServerSession]
    world = resources[WorldECS]
    player_addr = get_rpc_caller_addr()

    player_ent = session.players.get(player_addr)
    if player_ent is None:
        return
    elif not world.has_components(player_ent, Position, Velocity):
        return
    
    pos, vel = world.get_components(player_ent, Position, Velocity)
    pos.set_position(pos_x, pos_y)
    vel.set_velocity(*unpack_velocity(vel_angle, vel_length))

SERVER_RPCS = (
    control_player,
)