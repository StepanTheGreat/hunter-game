from plugin import Plugin, Resources

from core.ecs import WorldECS
from plugins.shared.collisions import CollisionEvent, StaticCollider

from plugins.shared.entities.projectile import Projectile

from plugins.shared.components import *

def deal_damage_on_collision(resources: Resources, event: CollisionEvent):
    world = resources[WorldECS]

    projectile_entity, target_entity = event.sensor_entity, event.hit_entity

    if not world.contains_entities(target_entity, projectile_entity):
        return

    # First we make sure that the sensor entity is a projectile

    if world.has_component(projectile_entity, Projectile):
        if event.hit_collider_ty is StaticCollider:
            # The projectile has hit a wall - kill him!
            world.remove_entity(projectile_entity)
        elif world.has_components(target_entity, Hittable, Team, Health):
            projectile_team, projectile = world.get_components(projectile_entity, Team, Projectile)
            target_team, target_health = world.get_components(target_entity, Team, Health)

            # If they are on the same team however - we won't do anything
            if not projectile_team.same_team(target_team):
                target_health.hurt(projectile.damage)
                print(f"Hurting entity {target_entity} with {projectile.damage}")

                # Our projectile can hit multiple targets, which is called piercing!
                projectile.consume_pierce()
                if not projectile.can_pierce():
                    world.remove_entity(projectile_entity)

class ServerProjectilePlugin(Plugin):
    def build(self, app):
        app.add_event_listener(CollisionEvent, deal_damage_on_collision)