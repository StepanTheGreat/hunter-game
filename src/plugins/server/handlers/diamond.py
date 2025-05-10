from plugin import Plugin, Resources

from core.ecs import WorldECS

from plugins.server.events import DiamondPickedUpEvent

from plugins.server.components import Diamond

def on_diamond_pickup(resources: Resources, event: DiamondPickedUpEvent):
    world = resources[WorldECS]

    diamond_ent = event.ent

    if world.contains_entity(diamond_ent):
        with world.command_buffer() as cmd:
            cmd.remove_entity(diamond_ent)

    if len(world.query_component(Diamond)) == 0:
        print("The robber team has won!")

class DiamondHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(DiamondPickedUpEvent, on_diamond_pickup)