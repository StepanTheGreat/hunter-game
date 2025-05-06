from plugin import Plugin, Resources

from core.ecs import WorldECS
from plugins.shared.collisions import CollisionEvent, StaticCollider
from plugins.shared.entities.projectile import Projectile, ProjectileHitEvent

from plugins.shared.components import *

def deal_damage_on_projectile_hit(resources: Resources, event: ProjectileHitEvent):
    world = resources[WorldECS]

    target_ent = event.target_ent
    if world.contains_entity(target_ent):
        target_health = world.get_component(target_ent, Health)

        target_health.hurt(event.damage)
        print(f"Hurting entity {target_ent} with {event.damage}")

class ServerProjectilePlugin(Plugin):
    def build(self, app):
        app.add_event_listener(ProjectileHitEvent, deal_damage_on_projectile_hit)