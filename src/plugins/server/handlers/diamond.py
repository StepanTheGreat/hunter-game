from plugin import Plugin, Resources, EventWriter

from core.ecs import WorldECS

from plugins.server.events import DiamondPickedUpEvent, GameStartedEvent, LightsOnEvent, GameFinishedEvent
from plugins.server.components import Diamond, Position, DiamondSpawnpoint
from plugins.server.actions import *

from plugins.shared.services.uidman import EntityUIDManager
from plugins.server.services.state import GameState, CurrentGameState, LightsOn

from plugins.shared.entities import make_diamond

def on_diamond_pickup(resources: Resources, event: DiamondPickedUpEvent):
    world = resources[WorldECS]
    state = resources[CurrentGameState]
    ewriter = resources[EventWriter]
    dispatcher = resources[ServerActionDispatcher]

    diamond_ent = event.ent

    if world.contains_entity(diamond_ent):
        with world.command_buffer() as cmd:
            cmd.remove_entity(diamond_ent)

    # This is a really ugly way of structuring it, but essentially...
    if state == GameState.InGame:
        # If the game has started
        
        if LightsOn not in resources:
            ewriter.push_event(LightsOnEvent())
            dispatcher.dispatch_action(GameNotificationAction(GameNotification.LightsOn))

        if len(world.query_component(Diamond)) == 0:
            dispatcher.dispatch_action(GameNotificationAction(GameNotification.RobberWon))
            ewriter.push_event(GameFinishedEvent())

def on_start_game_command(resources: Resources, _):
    "When the game starts, we would like to spawn diamonds across the map!"

    action_dispatcher = resources[ServerActionDispatcher]
    world = resources[WorldECS]
    uidman = resources[EntityUIDManager]

    diamond_entries = []

    diamond_spawnpoints = world.query_component(Position, including=DiamondSpawnpoint)

    assert len(diamond_spawnpoints) > 0, "No diamond spawnpoints provided on the map!"

    for _, spawnpoint in diamond_spawnpoints:
        diamond_pos = spawnpoint.get_position()
        diamond_pos = (diamond_pos.x, diamond_pos.y)

        uid = uidman.consume_entity_uid()
        diamond_entries.append((uid, diamond_pos))
        world.create_entity(*make_diamond(uid, diamond_pos))

    action_dispatcher.dispatch_action(SpawnDiamondsAction(tuple(diamond_entries)))

class DiamondHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(DiamondPickedUpEvent, on_diamond_pickup)
        app.add_event_listener(GameStartedEvent, on_start_game_command)