from plugin import Plugin, Resources, Schedule

from core.time import Clock
from core.ecs import WorldECS

from plugins.shared.components import *

def shoot_weapons_system(resources: Resources):
    world = resources[WorldECS]

    dt = resources[Clock].get_fixed_delta()

    with world.command_buffer() as cmd:
        for ent, (pos, angle, weapon) in world.query_components(Position, Angle, Weapon):
            weapon.update(dt)


            # If the shooting entity has a damage multiplier component - we're going to multiply
            # its damage. If not - we'll keep it at 1
            damage_multiplier = 1
            if world.has_component(ent, DamageMultiplier):
                damage_multiplier = world.get_component(ent, DamageMultiplier).by

            if weapon.may_shoot():
                # Safety: projectiles don't contain neither Angle nor Weapon components, thus it is safe
                # to create them in this iteration 
                cmd.create_entity(*
                    weapon.shoot(pos.get_position(), angle.get_vector(), damage_multiplier)
                )

class WeaponSystemsPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.FixedUpdate, shoot_weapons_system)