from plugin import Resources, event, EventWriter

from modules.utils import sliding_window

from plugins.shared.network import rpc, rpc_raw

@event
class MoveNetsyncedEntitiesCommand:
    """
    A client command send from the server that tells the client to move all specified entities to their
    new position (and update their velocities)
    """
    def __init__(self, entries: tuple[tuple[int, tuple[int, int], tuple[float, float]]]):
        self.entries = tuple[tuple[int, tuple[int, int], tuple[float, float]]]

@event
class SpawnPlayerCommand:
    """
    The command to spawn a player under specific UID on a specific position. The player
    sent can also be `main`, which means that the server has sent us our own player.
    """
    def __init__(self, uid: int, pos: tuple[int, int], is_main: bool):
        self.uid = uid
        self.pos = pos
        self.is_main = is_main

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
    ewriter = resources[EventWriter]

    movable_byte_size = MOVABLE_STRUCT_FORMAT.size

    # This map contains all network UIDs that were affected.

    moved_entries = []
    for entity_data in sliding_window(data, movable_byte_size):
        if len(entity_data) < movable_byte_size:
            break

        try:
            (uid, posx, posy, vel_angle, vel_len) = MOVABLE_STRUCT_FORMAT.unpack(entity_data)
            moved_entries.append((uid, (posx, posy), unpack_velocity(vel_angle, vel_len)))
        except struct.error:
            print("Failed to parse the entity movement packet")
            break
    
    if len(moved_entries) > 0:
        ewriter.push_event(MoveNetsyncedEntitiesCommand(
            tuple(entries)
        ))

@rpc("Hhh?", reliable=True)
def spawn_player(resources: Resources, uid: int, posx: int, posy: int, is_main: bool):
    ewriter = resources[EventWriter]

    ewriter.push_event(SpawnPlayerCommand(
        uid, (posx, posy), is_main
    ))

CLIENT_RPCS = (
    move_netsynced_entities,
    spawn_player
)
"RPCs used by the client"