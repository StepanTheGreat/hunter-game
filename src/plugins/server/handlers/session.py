from plugin import Plugin, Schedule, Resources, EventWriter


from core.time import SystemScheduler
from core.ecs import WorldECS

from plugins.server.events import AddedClientEvent, RemovedClientEvent, GameStartedEvent
from plugins.server.commands import CrookifyRandomPlayerCommand, StartGameCommand

from plugins.server.components import Client, OwnedByClient, NetEntity, Position, OwnsEntity, IsReady
from plugins.server.entities.characters import make_server_policeman
from plugins.shared.entities.diamond import make_diamond
from plugins.shared.services.uidman import EntityUIDManager
from plugins.shared.services.network import Server

from plugins.rpcs.server import SignalPlayerReadyCommand

from plugins.server.actions import ServerActionDispatcher, SpawnPlayerAction, SpawnDiamondsAction, TellReadyPlayersAction

from plugins.server.services.state import CurrentGameState, GameState
from plugins.server.services.clientlist import ClientList

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


def on_added_client(resources: Resources, event: AddedClientEvent):
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

    print("A new client connected:", new_client_ent)

    # First we're going to send the client all existing players in the world
    for _, (old_uid, old_pos) in world.query_components(NetEntity, Position, including=OwnedByClient):
        pos = old_pos.get_position()
        old_uid = old_uid.get_uid()

        action_dispatcher.dispatch_action(SpawnPlayerAction(
            new_client_ent, old_uid, (pos.x, pos.y), False
        ))

    # Now we're going to create the client's player and put it in the world
    player_ent = world.create_entity(
        *make_server_policeman(new_client_ent, new_player_uid, new_player_pos)
    )

    # Bind it to our client entity to create a parent-child relationship
    world.add_components(new_client_ent, OwnsEntity(player_ent))

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

def on_removed_client(resources: Resources, event: RemovedClientEvent):
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

    state = resources[CurrentGameState]
    world = resources[WorldECS]
    scheduler = resources[SystemScheduler]
    dispatcher = resources[ServerActionDispatcher]

    if state != GameState.WaitingForPlayers:
        return

    # First remove our current scheduled system, if it's present
    scheduler.remove_scheduled(start_game_system)

    clients_len = len(world.query_component(Client))
    ready_clients_len = len(world.query_component(Client, including=IsReady))

    dispatcher.dispatch_action(TellReadyPlayersAction(ready_clients_len, clients_len))

    if ready_clients_len > 1 and ready_clients_len == clients_len:
        WAIT_TIME = 10

        print(f"Scheduled next game start for {WAIT_TIME}s")
        scheduler.schedule_seconds(start_game_system, WAIT_TIME, False)
    else:
        print(f"Canceling game start")

def start_game_system(resources: Resources):
    "This is a scheduled system that is going to push the `GameStartedEvent`"

    ewriter = resources[EventWriter]

    print(f"The game has started!")

    ewriter.push_event(StartGameCommand())    
    ewriter.push_event(CrookifyRandomPlayerCommand())
    _spawn_diamonds(resources)

def on_client_ready(resources: Resources, command: SignalPlayerReadyCommand):
    clientlist = resources[ClientList]
    world = resources[WorldECS]

    if not clientlist.contains_client_addr(command.addr):
        return

    is_ready = command.is_ready
    client_ent = clientlist.get_client_ent(command.addr)

    has_is_ready_component = world.has_component(client_ent, IsReady)

    if is_ready and not has_is_ready_component:
        world.add_components(client_ent, IsReady())
    elif not is_ready and has_is_ready_component:
        world.remove_components(client_ent, IsReady)

    _reschedule_game_start(resources)

def on_game_started(resources: Resources, _):
    resources[Server].accept_incoming_connections(False)

class SessionHandlersPlugin(Plugin):
    def build(self, app):
        print("Executing the session events plugin")
        app.add_event_listener(AddedClientEvent, on_added_client)
        app.add_event_listener(RemovedClientEvent, on_removed_client)

        app.add_event_listener(GameStartedEvent, on_game_started)
        app.add_event_listener(SignalPlayerReadyCommand, on_client_ready)