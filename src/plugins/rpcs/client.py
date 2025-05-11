from plugin import Resources, event, EventWriter

from plugins.shared.services.network import ENDIAN, rpc, rpc_raw
from plugins.shared.interfaces.stage import GameNotification

from .pack import unpack_angle

import struct

@event
class SyncPlayersCommand:
    """
    A client command send from the server that tells the client to move all specified players to their
    new position, angles and shooting status
    """
    def __init__(self, entries: tuple[tuple[int, tuple[int, int], int, bool]]):
        self.entries: tuple[tuple[int, tuple[int, int], int, bool]] = entries

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
class SpawnDiamondsCommand:
    """
    The command to spawn diamonds. It contains a tuple of tuples: `(uid, (posx, posy))`
    """
    def __init__(self, diamonds: tuple[tuple[int, tuple[int, int]]]):
        self.diamonds = diamonds

@event
class KillEntityCommand:
    "The command to kill a network entity under the provided UID"
    def __init__(self, uid: int):
        self.uid = uid

@event
class CrookifyPolicemanCommand:
    "A command that turns an existing player (policeman) into a robber player"
    def __init__(self, uid: int):
        self.uid = uid

@event
class SyncTimeCommand:
    "The command to syncronize the current client's time with this new one"
    def __init__(self, time: float):
        self.time = time

@event
class SyncHealthCommand:
    "The command to syncronize the current player's health percentage to the one provided"
    def __init__(self, health: float):
        self.health = health

@event
class PlayersReadyCommand:
    "The command that tells the client how many players are ready to start the game"

    def __init__(self, players_ready: int, players: int):
        self.players_ready = players_ready
        self.players = players

@event
class GameNotificationCommand:
    "A notification send by the server"

    def __init__(self, notification: GameNotification):
        self.notification = notification

MOVE_PLAYERS_LIMIT = 127
"We can transfer only 127 players per packet for now"

SYNC_PLAYERS_FORMAT = struct.Struct(ENDIAN+"HhhB?")
"""
Components:
- Player's UID: 2 bytes unsigned int, `H`
- Player's Position: 2 2-byte signed ints, `2h`
- Player's Angle: 1-byte unsigned int, `B`
- Player's shooting status: 1-byte boolean `?`
"""

SPAWN_DIAMONDS_FORMAT = struct.Struct(ENDIAN+"Hhh")
"""
Components:
- Entity UID: 2 bytes unsigned int, `H`
- Entity Position: 2 2-byte signed ints, `2h`
"""

@rpc_raw
def sync_players_rpc(resources: Resources, data: bytes):
    """
    Sync all players on the client side. This will both set their position, angle and shooting status.
    """
    ewriter = resources[EventWriter]

    moved_entries = []
    try:
        for (uid, posx, posy, angle, is_shooting) in SYNC_PLAYERS_FORMAT.iter_unpack(data):
            moved_entries.append((
                uid, 
                (posx, posy), 
                unpack_angle(angle),
                is_shooting
            ))
    except struct.error:
        print("Failed to parse players movement packet")
        return
    
    if len(moved_entries) > 0:
        ewriter.push_event(SyncPlayersCommand(tuple(moved_entries)))

@rpc("Hhh?", reliable=True)
def spawn_player_rpc(resources: Resources, uid: int, posx: int, posy: int, is_main: bool):
    ewriter = resources[EventWriter]

    ewriter.push_event(SpawnPlayerCommand(
        uid, (posx, posy), is_main
    ))

@rpc_raw(reliable=True)
def spawn_diamonds_rpc(resources: Resources, data: bytes):
    ewriter = resources[EventWriter]

    new_diamonds = ()
    try:
        new_diamonds = tuple(
            (uid, (posx, posy)) for uid, posx, posy in SPAWN_DIAMONDS_FORMAT.iter_unpack(data)
        )
    except struct.error:
        print("Failed to parse the entity movement packet")
        return
    
    if len(new_diamonds) > 0:
        ewriter.push_event(SpawnDiamondsCommand(new_diamonds))

@rpc("H", reliable=True)
def kill_entity_rpc(resources: Resources, uid: int):
    ewriter = resources[EventWriter]

    ewriter.push_event(KillEntityCommand(uid))

@rpc("H", reliable=True)
def crookify_policeman_rpc(resources: Resources, uid: int):
    ewriter = resources[EventWriter]

    ewriter.push_event(CrookifyPolicemanCommand(uid))

@rpc("f")
def sync_time_rpc(resources: Resources, time: float):
    resources[EventWriter].push_event(SyncTimeCommand(time))

@rpc("f")
def sync_player_health_rpc(resources: Resources, health: float):
    resources[EventWriter].push_event(SyncHealthCommand(health))

@rpc("BB")
def tell_players_ready_rpc(resources: Resources, ready_players: int, players: int):
    resources[EventWriter].push_event(PlayersReadyCommand(ready_players, players))

@rpc("B")
def game_notification_rpc(resources: Resources, notification: int):
    try:
        # Because the notification ID might not be the required field - we're going to 
        # use a try-except block here to make sure, before sending the notification.

        resources[EventWriter].push_event(GameNotificationCommand(
            GameNotification(notification)
        ))
    except ValueError:
        pass

CLIENT_RPCS = (
    sync_players_rpc,
    spawn_player_rpc,
    spawn_diamonds_rpc,
    kill_entity_rpc,
    crookify_policeman_rpc,
    sync_time_rpc,
    sync_player_health_rpc,
    tell_players_ready_rpc,
    game_notification_rpc
)
"RPCs used by the client"