from plugin import Resources

from core.ecs import WorldECS
from core.assets import AssetManager

from plugins.network import rpc, rpc_raw, only_client
from plugins.components import Position, Velocity

from modules.utils import sliding_window
import struct

from ..pack import unpack_velocity
from ..components import NetworkEntityMap

from plugins.entities.policeman import make_policeman
from plugins.entities.player import MainPlayer

MOVABLE_ENTITIES_LIMIT = 127
"We can transfer only 127 entities per packet for now"

MOVABLE_STRUCT_FORMAT = struct.Struct("!H2hB?")
"""
Components:
- Entity UID: 2 bytes unsigned int, `H`
- Entity Position: 2 2-byte signed ints, `2h`
- Entity Velocity: 1-byte angle (will be then normalized to 360, though with some loss)
and a boolean value (that tells whether the vector is 0 or 1)
"""

@rpc_raw(reliable=False)
def move_netsynced_entities(resources: Resources, data: bytes):
    """
    Move all net-syncronized entities on the client side. This will both set their position and
    velocity.
    """
    world = resources[WorldECS]
    netmap = resources[NetworkEntityMap]

    movable_byte_size = MOVABLE_STRUCT_FORMAT.size

    # This map contains all network UIDs that were affected.

    for entity_data in sliding_window(data, movable_byte_size):
        if len(entity_data) < movable_byte_size:
            break

        try:
            (uid, posx, posy, vel_angle, vel_len) = MOVABLE_STRUCT_FORMAT.unpack(entity_data)
            ent = netmap.get_ent(uid)
            if ent is None:
                continue
            elif not world.has_components(ent, Position, Velocity):
                continue
            elif world.has_component(ent, MainPlayer):
                # We will for now do nothing with main players
                continue

            pos, vel = world.get_components(ent, Position, Velocity)
            pos.set_position(posx, posy)
            vel.set_velocity(*unpack_velocity(vel_angle, vel_len))

        except struct.error:
            print("Failed to parse the entity movement packet")
            break

@rpc("Hhh?", reliable=True)
def spawn_player(resources: Resources, uid: int, posx: int, posy: int, ismain: bool):
    world = resources[WorldECS]
    assets = resources[AssetManager]

    print("Spawning the player!")

    world.create_entity(
        *make_policeman(uid, (posx, posy), ismain, assets)
    )

COMMON_RPCS = (
    
)
"RPCs shared across both pure and host clients. Use `CLIENT_ONLY_RPCS` or `CLIENT_HOST_RPCS` instead"

CLIENT_ONLY_RPCS: tuple = COMMON_RPCS + (
    move_netsynced_entities,
    spawn_player
)
"RPCs that can be used by pure clients"

CLIENT_HOST_RPCS: tuple = COMMON_RPCS
"RPCs that can be used by a client-host"