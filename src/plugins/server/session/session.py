from plugin import Plugin, Resources

from plugins.shared.network import Server, BroadcastWriter

from plugins.server.events import GameStartedEvent

from plugins.rpcs.server import SERVER_RPCS

from enum import Enum, auto
from typing import Optional

MAX_PLAYERS = 5
REQUIRES_PLAYERS = MAX_PLAYERS

WAIT_TIME_MAP = {
    2: 10,
    3: 60,
    4: 30,
    5: 15
}
"The amount of time the game must wait to start the game for every player count. If absent - it's infinite."

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

    def taken_player_slots(self) -> int:
        "How many player slots are available on this session?"
        
        return len(self.players)
    
    def enter_state(self, state: GameState):
        self.game_state = GameState.InGame

    def can_accept_new_players(self) -> int:
        "Can this server accept more players?"

        return len(self.players) < MAX_PLAYERS
    
    def has_game_started(self) -> bool:
        return self.game_state != GameState.WaitingForPlayers

def on_game_started(resources: Resources, _):
    session = resources[GameSession]
    server = resources[Server]

    # When the game starts, we would like to switch its game state and also close server connections
    session.enter_state(GameState.InGame)
    server.accept_incoming_connections(False)
    
class SessionContextPlugin(Plugin):
    def build(self, app):
        # In this plugin we're going to initialize the game session resource and the server
        app.insert_resource(GameSession())
        app.insert_resource(BroadcastWriter())
        app.insert_resource(Server(app.get_resources(), MAX_PLAYERS, SERVER_RPCS))

        app.add_event_listener(GameStartedEvent, on_game_started)