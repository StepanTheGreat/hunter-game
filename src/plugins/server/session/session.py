from plugin import Plugin, Schedule, Resources

from plugins.shared.network import Server
from plugins.rpcs.server import SERVER_RPCS

from modules.utils import Timer

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
    
class SessionContextPlugin(Plugin):
    def build(self, app):
        # In this plugin we're going to initialize the game session resource and the server
        app.insert_resource(GameSession())
        app.insert_resource(Server(app.get_resources(), MAX_PLAYERS, SERVER_RPCS))