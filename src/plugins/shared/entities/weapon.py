"""
This file contains a general use Weapon component that works for every single entity
"""
from plugin import Plugin, Resources, Schedule

<<<<<<< HEAD
from modules.time import Clock
=======
from core.time import Clock
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
from core.ecs import WorldECS, component

from plugins.shared.components import *

from .projectile import ProjectileFactory

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

def shoot_weapons(resources: Resources):
    world = resources[WorldECS]

    dt = resources[Clock].get_fixed_delta()

    with world.command_buffer() as cmd:
        for ent, (pos, angle, weapon) in world.query_components(Position, Angle, Weapon):
            weapon.update(dt)

            if weapon.may_shoot():
                # Safety: projectiles don't contain neither Angle nor Weapon components, thus it is safe
                # to create them in this iteration 
                cmd.create_entity(*
                    weapon.shoot(pos.get_position(), angle.get_vector())
                )

class WeaponPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.FixedUpdate, shoot_weapons)
    