from plugin import Plugin, Schedule, Resources

from plugins.shared.network import Server, ClientConnectedEvent, ClientDisconnectedEvent
from plugins.contracts.listener import notify_available_server, LISTENER_PORT
from plugins.contracts.server import SERVER_RPCS

from modules.time import Clock, Timer

from enum import Enum, auto
from typing import Optional

MAX_PLAYERS = 5
REQUIRES_PLAYERS = MAX_PLAYERS

BROADCAST_FREQUENCY = 5

class GameState(Enum):
    WaitingForPlayers = auto()
    InGame = auto()
    Finishing = auto()

class GameSession:
    def __init__(self):
        self.players: dict[tuple[str, int], Optional[int]] = {}
        """
        The client address to player's entity map. Generally, this acts more like a list
        of clients, but also contains direct mappings to client's entity.
        """

        self.game_state: GameState = GameState.WaitingForPlayers
        "The current state of the server's session"

        self.broadcast_timer = Timer(BROADCAST_FREQUENCY, True)

    def taken_player_slots(self) -> int:
        "How many player slots are available on this session?"
        
        return len(self.players)

    def can_accept_new_players(self) -> int:
        "Can this server accept more players?"

        return len(self.players) < MAX_PLAYERS

def broadcast_server(resources: Resources):
    session = resources[GameSession]
    server = resources[Server]
    dt = resources[Clock].get_delta()

    if session.game_state == GameState.WaitingForPlayers:
        broadcast_timer = session.broadcast_timer

        broadcast_timer.tick(dt)
        if broadcast_timer.has_finished():
            server.broadcast(
                LISTENER_PORT, 
                notify_available_server, 
                MAX_PLAYERS,
                session.taken_player_slots()
            )
            broadcast_timer.reset()

def on_client_connection(resources: Resources, event: ClientConnectedEvent):
    session = resources[GameSession]

    client_addr = event.addr
    if client_addr not in session.players:
        session.players[client_addr] = None
    
    print("A new client connection:", client_addr)

def on_client_disconnection(resources: Resources, event: ClientDisconnectedEvent):
    session = resources[GameSession]

    client_addr = event.addr
    if client_addr in session.players:
        del session.players[client_addr]
    
    print("A new client disconnection:", client_addr)

class GameSessionPlugin(Plugin):
    def build(self, app):
        app.insert_resource(GameSession())
        app.insert_resource(Server(app.get_resources(), MAX_PLAYERS, SERVER_RPCS))
        app.add_systems(Schedule.Update, broadcast_server)

        app.add_event_listener(ClientConnectedEvent, on_client_connection)
        app.add_event_listener(ClientDisconnectedEvent, on_client_disconnection)

