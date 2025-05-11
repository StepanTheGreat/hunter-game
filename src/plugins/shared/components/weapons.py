from core.ecs import component
from .base import *

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
            Projectile(self.damage, self.pierce),
            GameEntity()
        )

class WeaponStats:
    "This class contains actor-agnostic weapon statistics."
    def __init__(self, cooldown: float = 1, automatic: bool = False):
        self.cooldown = cooldown
        self.automatic = automatic

@component
class Weapon:
    def __init__(
        self, 
        projectile_factory: ProjectileFactory, 
        stats: WeaponStats,
    ):
        self.projectile_factory = projectile_factory
        self.cooldown = stats.cooldown

        self.on_cooldown = self.cooldown

        self.is_shooting = False
        self.automatic = stats.automatic
        "When `True`, the `is_shooting` variable won't get reset to `False` automatically - only manually"

    def update(self, dt: float):
        if self.on_cooldown > 0:
            self.on_cooldown -= dt

    def may_shoot(self) -> bool:
        "Is the weapon's cooldown down AND it's actively used?"
        return self.is_shooting and self.on_cooldown <= 0
    
    def shoot(self, pos: tuple[float, float], direction: tuple[float, float]) -> tuple:
        "Reset all timers and produce a projectile to shoot"
        assert self.may_shoot(), "Can only shoot when the cooldown is down and the weapon is used"

        self.on_cooldown = self.cooldown
        if not self.automatic:
            self.is_shooting = False

        return self.projectile_factory.make_projectile(pos, direction)

    def start_shooting(self):
        self.is_shooting = True

    def stop_shooting(self):
        self.is_shooting = False