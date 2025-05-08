from plugin import Plugin, Resources, EventWriter

from core.ecs import WorldECS

from plugins.shared.components import *

from plugins.shared.events import CollisionEvent, ProjectileHitEvent

def collide_projectiles_system(resources: Resources, event: CollisionEvent):
    world = resources[WorldECS]
    ewriter = resources[EventWriter]

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
            target_team = world.get_component(target_entity, Team)

            # If they are on the same team however - we won't do anything
            if not projectile_team.same_team(target_team):

                # Because this entire collision resolution logic is shared, but only the hitting
                # part is up to the server - we're going to simply send an event instead
                ewriter.push_event(ProjectileHitEvent(target_entity, projectile.damage))

                # Our projectile can hit multiple targets, which is called piercing!
                projectile.consume_pierce()
                if not projectile.can_pierce():
                    world.remove_entity(projectile_entity)

class ProjectileSystemsPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(CollisionEvent, collide_projectiles_system)
