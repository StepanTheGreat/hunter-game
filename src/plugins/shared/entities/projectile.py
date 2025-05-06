from plugin import Plugin, Resources

from core.ecs import WorldECS, component
from plugins.shared.collisions import DynCollider, CollisionEvent, StaticCollider

from plugins.shared.components import *

from typing import Callable

@component
class Projectile:
    "A general projectile component"
    def __init__(self, damage: float, pierce: int = 1):
        assert damage >= 0, "Can't deal negative damage"
        assert pierce >= 1, "Pierce can't be less than 1"

        self.damage = damage
        self.pierce = pierce

    def can_pierce(self) -> bool:
        return self.pierce > 0

    def consume_pierce(self) -> bool:
        self.pierce -= 1
        
class ProjectileFactory:
    """
    This is more of a builder class used to build different types of projectiles.
    
    Before you use `user_components` though, please read how it works and how to use it properly
    """
    def __init__(
        self,
        is_enemy: bool,
        speed: float,
        radius: float,
        damage: int = 1,
        pierce: int = 1,
        lifetime: int = 10,
        spawn_offset: float = 0,
        user_components: tuple[Callable, ...] = ()
    ):
        self.is_enemy = is_enemy
        self.speed = speed
        self.radius = radius
        self.damage = damage
        self.lifetime = lifetime
        self.pierce = pierce

        self.user_components: tuple[Callable, ...] = user_components
        """
        User components are user-defined components, attached to this projectile factory.
        Attention - here, you bind not objects, but functions without arguments that return
        said objects (essentially lambdas: `lambda: MyComp()`).
        
        The reasoning is simple - we don't want shared components to be persistent across multiple
        projectiles, so this workaround is going to "construct" said projectiles every single time
        instead.
        """

        self.spawn_offset = spawn_offset
        "This attribute describes the offset the projectile is going to move when spawning. Useful for melee weapons for example"

    def copy(self) -> "ProjectileFactory":
        "Create a copy of this projectile factory"
        
        return ProjectileFactory(
            self.is_enemy,
            self.speed,
            self.radius,
            self.damage,
            self.pierce,
            self.lifetime,
            self.spawn_offset,
            self.user_components
        )

    def make_projectile(self, pos: tuple[float, float], direction: tuple[float, float]) -> tuple:
        "Construct a projectile component bundle (ready to spawn)"
        
        pos = (pos[0] + direction[0]*self.spawn_offset, pos[1] + direction[1]*self.spawn_offset)

        return (
            Position(*pos),
            Velocity(*direction, self.speed),
            DynCollider(self.radius, 1, sensor=True),
            Temporary(self.lifetime),
            Team(self.is_enemy),

            # For every user component function, we're going to call it and collect into our components
            *(user_comp() for user_comp in self.user_components),
            Projectile(self.damage, self.pierce)
        )

def make_projectile(
    factory: ProjectileFactory,
    pos: tuple[float, float], 
    direction: tuple[float, float], 
) -> tuple:
    return factory.make_projectile(pos, direction)

@event
class ProjectileHitEvent:
    "Fired whenever a projectile hits a hittable entity of an opposite team"

    def __init__(self, target_ent: int, damage: float):
        self.target_ent = target_ent
        self.damage = damage

def collide_projectiles(resources: Resources, event: CollisionEvent):
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

class ProjectilePlugin(Plugin):
    def build(self, app):
        app.add_event_listener(CollisionEvent, collide_projectiles)
