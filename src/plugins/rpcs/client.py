from plugin import Resources, event, EventWriter

from plugins.shared.network import ENDIAN, rpc, rpc_raw

from .pack import unpack_velocity

import struct

@event
class MoveNetsyncedEntitiesCommand:
    """
    A client command send from the server that tells the client to move all specified entities to their
    new position (and update their velocities)
    """
    def __init__(self, entries: tuple[tuple[int, tuple[int, int]]]):
        self.entries: tuple[tuple[int, tuple[int, int]]] = entries

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

@event
class KillEntityCommand:
    "The command to kill a network entity under the provided UID"
    def __init__(self, uid: int):
        self.uid = uid

@event
class SyncTimeCommand:
    "The command to syncronize the current client's time with this new one"
    def __init__(self, time: float):
        self.time = time

MOVE_NETSYNCED_ENTITIES_LIMIT = 127
"We can transfer only 127 entities per packet for now"

MOVE_NETSYNCED_ENTITIES_FORMAT = struct.Struct(ENDIAN+"H2h")
"""
Components:
- Entity UID: 2 bytes unsigned int, `H`
- Entity Position: 2 2-byte signed ints, `2h`
"""

@rpc_raw
def move_netsynced_entities_rpc(resources: Resources, data: bytes):
    """
    Move all net-syncronized entities on the client side. This will both set their position and
    velocity.
    """
    ewriter = resources[EventWriter]

    moved_entries = []
    try:
        for (uid, posx, posy,) in MOVE_NETSYNCED_ENTITIES_FORMAT.iter_unpack(data):
            moved_entries.append((
                uid, 
                (posx, posy), 
            ))
    except struct.error:
        print("Failed to parse the entity movement packet")
        return
    
    if len(moved_entries) > 0:
        ewriter.push_event(MoveNetsyncedEntitiesCommand(
            tuple(moved_entries)
        ))

@rpc("Hhh?", reliable=True)
def spawn_player_rpc(resources: Resources, uid: int, posx: int, posy: int, is_main: bool):
    ewriter = resources[EventWriter]

    ewriter.push_event(SpawnPlayerCommand(
        uid, (posx, posy), is_main
    ))

@rpc("H", reliable=True)
def kill_entity_rpc(resources: Resources, uid: int):
    ewriter = resources[EventWriter]

    ewriter.push_event(KillEntityCommand(uid))

@rpc("f")
def sync_time_rpc(resources: Resources, time: float):
    resources[EventWriter].push_event(SyncTimeCommand(time))

CLIENT_RPCS = (
    move_netsynced_entities_rpc,
    spawn_player_rpc,
    kill_entity_rpc,
    sync_time_rpc
)
"RPCs used by the client"