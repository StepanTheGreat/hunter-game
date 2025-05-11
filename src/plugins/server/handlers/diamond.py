from plugin import Plugin, Resources

from core.ecs import WorldECS

from plugins.server.events import DiamondPickedUpEvent, GameStartedEvent
from plugins.server.components import Diamond, Position, DiamondSpawnpoint
from plugins.server.actions import ServerActionDispatcher, SpawnDiamondsAction

from plugins.shared.services.uidman import EntityUIDManager
from plugins.shared.entities import make_diamond


def on_diamond_pickup(resources: Resources, event: DiamondPickedUpEvent):
    world = resources[WorldECS]

    diamond_ent = event.ent

    if world.contains_entity(diamond_ent):
        with world.command_buffer() as cmd:
            cmd.remove_entity(diamond_ent)

    if len(world.query_component(Diamond)) == 0:
        print("The robber team has won!")

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