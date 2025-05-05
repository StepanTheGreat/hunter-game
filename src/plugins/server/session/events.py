from plugin import Plugin, Schedule, Resources

from plugins.shared.network import ClientConnectedEvent, ClientDisconnectedEvent

from core.ecs import WorldECS
from plugins.shared.entities.policeman import make_policeman
from plugins.shared.components import EntityUIDManager

from ..actions import ServerActionDispatcher, SpawnPlayerAction


from .session import GameSession

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

class SessionEventsPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(ClientConnectedEvent, on_client_connection)
        app.add_event_listener(ClientDisconnectedEvent, on_client_disconnection)