"""
Everything related to server-side logic, be it from managing the game session, to components, systems
and so on.
"""

from plugin import Plugin, Schedule, Resources
from plugins.network import only_server, ClientConnectedEvent, ClientDisconnectedEvent, Server

from core.pg import Clock
from core.ecs import WorldECS, ComponentsRemovedEvent

from modules.utils import Timer

from ..listener import notify_available_server

from .rpcs import SERVER_RPCS

from enum import Enum, auto
from typing import Optional

class GameState(Enum):
    WaitingForPlayers = auto()
    "The server is waiting until the game has started, either by the main player, or by getting finding all players"
    InGame = auto()
    "The game is currently running"
    EndGame = auto()
    "The game has finished, usually this state only exists to send people game results and close after a second"

class ServerSession:
    """
    The server session object itself. It's responsible for mapping players to their entities, storing
    the current state of the session (has the game started or not) and more.

    This object is used solely by the server, as it is its own state machine
    """

    GAME_TIME_LIMIT = 10*60 # 10 minutes
    BROADCAST_FREQUENCY = 8

    def __init__(self, game_owner: tuple[str, int]):
        self.players: dict[tuple[str, int], Optional[int]] = {}
        self.game_owner: tuple[str, int] = game_owner

        self.game_state = GameState.WaitingForPlayers

        self.broadcast_timer = Timer(8, True)
        self.time_passed = 0

    def reset(self):
        "Reset the server session. Should be called every time a new session is created"
        self = ServerSession()

    def is_game_owner(self, addr: tuple[str, int]) -> bool:
        return self.game_owner == addr

    def has_game_started(self) -> bool:
        return self.game_state != GameState.WaitingForPlayers

def on_client_connection(resources: Resources, event: ClientConnectedEvent):
    session = resources[ServerSession]
    world = resources[WorldECS]

    if session.has_game_started():
        return
    
    print("Client connected to the server: {}")
    # We should create a new 

def on_client_disconnection(resources: Resources, event: ClientDisconnectedEvent):
    session = resources[ServerSession]
    world = resources[WorldECS]

    if event.addr in session.players:
        ent = session.players[event.addr]

        if ent is not None:
            with world.command_buffer() as cmd:
                cmd.remove_entity(ent)
            # TODO: Delete the entity on all clients as well
                

@only_server
def broadcast_server(resources: Resources):
    "If the server hasn't even started the game - it's going to broacast itself to clients on the LAN"

    session = resources[ServerSession]
    dt = resources[Clock].get_fixed_delta()

    if not session.has_game_started():
        session.broadcast_timer.tick(dt)

        if session.broadcast_timer.has_finished():
            resources[Server].broadcast(
                1524, 
                notify_available_server,
                5-len(session.players)
            )
            session.broadcast_timer.reset()

class ServerPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.FixedUpdate, broadcast_server)