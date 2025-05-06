from plugin import Plugin, Schedule, Resources, EventWriter

from plugins.shared.network import ClientConnectedEvent, ClientDisconnectedEvent

from core.time import SystemScheduler
from core.ecs import WorldECS
from plugins.shared.entities.policeman import make_policeman
from plugins.shared.components import EntityUIDManager

from ..actions import ServerActionDispatcher, SpawnPlayerAction

from .session import GameSession, GameStartedEvent, WAIT_TIME_MAP

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

    action_dispatcher.dispatch_action(SpawnPlayerAction(
        new_client_addr, new_player_uid, new_player_pos, True
    ))

    # We'll iterate all our previous clients
    for old_addr, old_ent in session.players.items():
        # Send to them our new created player
        action_dispatcher.dispatch_action(SpawnPlayerAction(
            old_addr, new_player_uid, new_player_pos, False
        ))

        # If this old client got an entity - we're going to send it to our new player
        if old_ent is None:
            continue

        old_uid = uidman.get_uid(old_ent)
        if old_uid is None:
            continue 

        action_dispatcher.dispatch_action(SpawnPlayerAction(
            new_client_addr, old_uid, (0, 0), False
        ))

    if new_client_addr not in session.players:
        session.players[new_client_addr] = new_player_ent
    
    print("A new client connection:", new_client_addr)

    reschedule_game_start(resources)

def on_client_disconnection(resources: Resources, event: ClientDisconnectedEvent):
    world = resources[WorldECS]
    session = resources[GameSession]

    client_addr = event.addr
    if client_addr in session.players:
        client_ent = session.players[client_addr]

        # If this client got an entity - we would like to remove it from the world
        if client_ent is not None and world.contains_entity(client_ent):
            with world.command_buffer() as cmd:
                cmd.remove_entity(client_ent)
        
        # While also deleting it from the client list
        del session.players[client_addr]
    
    print("A new client disconnection:", client_addr)

    reschedule_game_start(resources)

def reschedule_game_start(resources: Resources):
    "This is a helper function that will schedule a new game start based on the current amount of players"

    session = resources[GameSession]
    scheduler = resources[SystemScheduler]

    if session.has_game_started():
        return

    # First remove our current scheduled system, if it's present
    scheduler.remove_scheduled(start_game)

    # Because wait time can be `None` (infinite), we will need to check that as well
    wait_time = WAIT_TIME_MAP.get(len(session.players))
    if wait_time is not None:
        # If it's okay - schedule the start game
        print(f"Scheduled next game start for {wait_time}s")
        scheduler.schedule_seconds(start_game, wait_time, False)

def start_game(resources: Resources):
    "This is a scheduled system that is going to push the `GameStartedEvent`"

    print(f"The game has started!")
    resources[EventWriter].push_event(GameStartedEvent())

class SessionEventsPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(ClientConnectedEvent, on_client_connection)
        app.add_event_listener(ClientDisconnectedEvent, on_client_disconnection)