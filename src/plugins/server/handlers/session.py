from plugin import Plugin, Schedule, Resources, EventWriter


from core.time import SystemScheduler
from core.ecs import WorldECS

from plugins.server.events import AddedClient, RemovedClient, GameStartedEvent
from plugins.server.commands import CrookifyRandomPlayerCommand, StartGameCommand

from plugins.server.components import Client, OwnedByClient, NetEntity, Position
from plugins.server.entities.characters import make_server_policeman
from plugins.shared.entities.diamond import make_diamond
from plugins.shared.services.uidman import EntityUIDManager
from plugins.shared.services.network import Server

from plugins.server.actions import ServerActionDispatcher, SpawnPlayerAction, SpawnDiamondsAction

from plugins.server.services.state import GameState

from plugins.server.constants import WAIT_TIME_MAP

def _spawn_diamonds(resources: Resources):
    "A function purely for testing purposes"
    action_dispatcher = resources[ServerActionDispatcher]
    world = resources[WorldECS]
    uidman = resources[EntityUIDManager]

    diamond_entries = []
    for diamond_pos in ((0, 0), (64, 0), (-64, 0), (0, 64), (0, -64)):
        uid = uidman.consume_entity_uid()

        diamond_entries.append((uid, diamond_pos))

        world.create_entity(*make_diamond(uid, diamond_pos))

    action_dispatcher.dispatch_action(SpawnDiamondsAction(tuple(diamond_entries)))


def on_added_client(resources: Resources, event: AddedClient):
    """
    When a new client gets added, we would like to create an entity for it and also reschedule
    our game start.
    """

    world = resources[WorldECS]
    uidman = resources[EntityUIDManager]
    action_dispatcher = resources[ServerActionDispatcher]


    new_client_ent = event.ent
    new_player_uid = uidman.consume_entity_uid()
    new_player_pos = (0, 0)

    # First we're going to send the client all existing players in the world
    for _, (old_uid, old_pos) in world.query_components(NetEntity, Position, including=OwnedByClient):
        pos = old_pos.get_position()

        action_dispatcher.dispatch_action(SpawnPlayerAction(
            new_client_ent, old_uid, (pos.x, pos.y), False
        ))

    # Now we're going to create the client's player and put it in the world
    new_player_ent = world.create_entity(
        *make_server_policeman(new_client_ent, new_player_uid, new_player_pos)
    )   

    # Send it over to our own client
    action_dispatcher.dispatch_action(SpawnPlayerAction(
        new_client_ent, new_player_uid, new_player_pos, True
    ))

    # And now send our new entity to all the other old clients

    for old_ent, _ in world.query_component(Client):
        if old_ent == new_client_ent:
            continue
        
        action_dispatcher.dispatch_action(SpawnPlayerAction(
            old_ent, new_player_uid, new_player_pos, False
        ))
    
    print("A new client connection:", event.addr)

    _reschedule_game_start(resources)

def on_removed_client(resources: Resources, event: RemovedClient):
    """
    When a client is removed from the world, it means we need to kill its owned entity.
    We're going to iterate all owned entities by the clients, and if IDs match - kill them.
    """

    world = resources[WorldECS]

    with world.command_buffer() as cmd:
        for owned_ent, owned_by in world.query_component(OwnedByClient):
            if owned_by.get_client_ent() == event.ent:
                cmd.remove_entity(owned_ent)
    
    print("A new client disconnection:", event.addr)

    _reschedule_game_start(resources)

def _reschedule_game_start(resources: Resources):
    "This is a helper function that will schedule a new game start based on the current amount of players"

    state = resources[GameState]
    world = resources[WorldECS]
    scheduler = resources[SystemScheduler]

    if state is not GameState.WaitingForPlayers:
        return

    # First remove our current scheduled system, if it's present
    scheduler.remove_scheduled(start_game_system)

    clients_len = len(world.query_component(Client))

    # Because wait time can be `None` (infinite), we will need to check that as well
    wait_time = WAIT_TIME_MAP.get(clients_len)
    if wait_time is not None:
        # If it's okay - schedule the start game
        print(f"Scheduled next game start for {wait_time}s")
        scheduler.schedule_seconds(start_game_system, wait_time, False)

def start_game_system(resources: Resources):
    "This is a scheduled system that is going to push the `GameStartedEvent`"

    ewriter = resources[EventWriter]

    print(f"The game has started!")

    ewriter.push_event(StartGameCommand())    
    ewriter.push_event(CrookifyRandomPlayerCommand())

def on_game_started(resources: Resources, _):


    resources[Server].accept_incoming_connections(False)

class SessionEventsPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(AddedClient, on_added_client)
        app.add_event_listener(RemovedClient, on_removed_client)