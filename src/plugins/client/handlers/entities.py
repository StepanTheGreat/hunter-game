from plugin import Plugin, Resources

from plugins.client.commands import CleanUpEntitiesCommand

from core.ecs import WorldECS

from plugins.client.components import GameEntity

def on_entity_cleanup(resources: Resources, command: CleanUpEntitiesCommand):
    "When the game is over, we would like to clean up ALL existing game entities"

    world = resources[WorldECS]
    
    with world.command_buffer() as cmd:
        for ent, _ in world.query_component(GameEntity):
            world.remove_entity(ent)

class EntitiesHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(CleanUpEntitiesCommand, on_entity_cleanup)