<<<<<<< HEAD
from plugin import Plugin, Schedule, Resources

from plugins.shared.network import Server, ClientConnectedEvent, ClientDisconnectedEvent
from plugins.rpcs.listener import notify_available_server_rpc, LISTENER_PORT
from plugins.rpcs.server import SERVER_RPCS

from core.ecs import WorldECS
from plugins.shared.entities.policeman import make_policeman
from plugins.shared.components import EntityUIDManager

from ..actions import ServerActionDispatcher, SpawnPlayerAction

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
                notify_available_server_rpc, 
                MAX_PLAYERS,
                session.taken_player_slots()
            )
            broadcast_timer.reset()

def on_client_connection(resources: Resources, event: ClientConnectedEvent):
    session = resources[GameSession]
    world = resources[WorldECS]
    uidman = resources[EntityUIDManager]
    action_dispatcher = resources[ServerActionDispatcher]

    new_client_addr = event.addr
    new_player_uid = uidman.consume_entity_uid()
    new_player_pos = (0, 0)

    new_player_ent = world.create_entity(
        *make_policeman(new_player_uid, new_player_pos)
    )   

    # We'll iterate all our previous clients
    for old_addr, old_ent in session.players.items():
        # Send to them our new created player
        action_dispatcher.dispatch_action(SpawnPlayerAction(
            old_addr, new_player_uid, new_player_pos, False
        ))

        # If this old client got an entity - we're going to send it to our new player
        if old_ent is not None:
            old_uid = uidman.get_uid(old_ent)
            action_dispatcher.dispatch_action(SpawnPlayerAction(
                new_client_addr, old_uid, (0, 0), False
            ))
    
    action_dispatcher.dispatch_action(SpawnPlayerAction(
        new_client_addr, new_player_uid, new_player_pos, True
    ))

    if new_client_addr not in session.players:
        session.players[new_client_addr] = new_player_ent
    
    print("A new client connection:", new_client_addr)

def on_client_disconnection(resources: Resources, event: ClientDisconnectedEvent):
    world = resources[WorldECS]
    session = resources[GameSession]

    client_addr = event.addr
    if client_addr in session.players:
        client_ent = session.players[client_addr]

        # If this client got an entity - we would like to remove it from the world
        if client_ent is not None:
            with world.command_buffer() as cmd:
                cmd.remove_entity(client_ent)
        
        # While also deleting it from the client list
        del session.players[client_addr]
    
    print("A new client disconnection:", client_addr)

class GameSessionPlugin(Plugin):
    def build(self, app):
        app.insert_resource(GameSession())
        app.insert_resource(Server(app.get_resources(), MAX_PLAYERS, SERVER_RPCS))
        app.add_systems(Schedule.Update, broadcast_server)

        app.add_event_listener(ClientConnectedEvent, on_client_connection)
        app.add_event_listener(ClientDisconnectedEvent, on_client_disconnection)
=======
from plugin import Plugin

from .session import SessionContextPlugin
from .events import SessionEventsPlugin
from .systems import SessionSystemsPlugin


class SessionPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            SessionContextPlugin(),
            SessionEventsPlugin(),
            SessionSystemsPlugin()
        )
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75

