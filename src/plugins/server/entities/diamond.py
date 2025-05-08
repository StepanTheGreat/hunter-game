from plugin import Plugin, Schedule, Resources

from core.ecs import WorldECS

from plugins.shared.events import DiamondPickedUpEvent

def on_diamond_pickup(resources: Resources, event: DiamondPickedUpEvent):
    world = resources[WorldECS]

    diamond_ent = event.ent

    if world.contains_entity(diamond_ent):
        with world.command_buffer() as cmd:
            cmd.remove_entity(diamond_ent)

class ServerDiamondPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(DiamondPickedUpEvent, on_diamond_pickup)