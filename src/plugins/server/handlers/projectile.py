from plugin import Plugin, Resources

from core.ecs import WorldECS

from plugins.shared.events import ProjectileHitEvent
from plugins.server.components import *

from plugins.server.actions import ServerActionDispatcher, SyncHealthAction

def deal_damage_on_projectile_hit(resources: Resources, event: ProjectileHitEvent):
    world = resources[WorldECS]
    dispatcher = resources[ServerActionDispatcher]

    target_ent = event.target_ent
    if world.contains_entity(target_ent):
        target_health = world.get_component(target_ent, Health)

        # Hurt the entity
        target_health.hurt(event.damage)

        # But, if it's a player...
        if not world.has_component(target_ent, OwnedByClient):
            return

        client_ent = world.get_component(target_ent, OwnedByClient).get_client_ent()

        # And push a health syncronisation action, so it knows how much health it has 
        dispatcher.dispatch_action(SyncHealthAction(
            client_ent,
            target_health.get_percentage()
        ))

class ProjectileHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(ProjectileHitEvent, deal_damage_on_projectile_hit)