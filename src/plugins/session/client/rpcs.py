from plugin import Resources

from core.ecs import WorldECS

from plugins.network import rpc, rpc_raw, only_client
from plugins.components import Position, Velocity

from modules.utils import sliding_window
from struct import Struct

from ..pack import unpack_velocity
from ..components import NetEntity

MOVABLE_ENTITIES_LIMIT = 127
"We can transfer only 127 entities per packet for now"

MOVABLE_STRUCT_FORMAT = Struct("!H2hB?")
"""
Components:
- Entity UID: 2 bytes unsigned int, `H`
- Entity Position: 2 2-byte signed ints, `2h`
- Entity Velocity: 1-byte angle (will be then normalized to 360, though with some loss)
and a boolean value (that tells whether the vector is 0 or 1)
"""

@rpc_raw(reliable=False)
def move_netsynced_entities(resources: Resources, data: bytes):
    world = resources[WorldECS]

    movable_byte_size = MOVABLE_STRUCT_FORMAT.size

    uid_moved_map: dict[int, tuple[tuple[int, int], tuple[float, float]]] = {}
    # This map contains all network UIDs that were affected.

    for entity_data in sliding_window(data, movable_byte_size):
        if len(entity_data) < movable_byte_size:
            break
        
        try:
            (uid, posx, posy, vel_angle, vel_len) = MOVABLE_STRUCT_FORMAT.unpack(entity_data)
            uid_moved_map[uid] = (
                (posx, posy), 
                unpack_velocity(vel_angle, vel_len)
            )
        except:
            print("Failed to parse the entity movement packet")
            break

    # Now, we're going to iterate every entity and if its NetEntity 
    for _, (ent, pos, vel) in world.query_components(NetEntity, Position, Velocity):
        uid = ent.get_uid()
        if uid in uid_moved_map:
            new_pos, new_vel = uid_moved_map[uid]
            pos.set_position(*new_pos)
            vel.set_velocity(*new_vel)

COMMON_RPCS = (

)
"RPCs shared across both pure and host clients. Use `CLIENT_ONLY_RPCS` or `CLIENT_HOST_RPCS` instead"

CLIENT_ONLY_RPCS: tuple = COMMON_RPCS + (
    move_netsynced_entities,
)
"RPCs that can be used by pure clients"

CLIENT_HOST_RPCS: tuple = COMMON_RPCS
"RPCs that can be used by a client-host"