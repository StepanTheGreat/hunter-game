from plugin import Plugin, Resources, Schedule

from core.time import Clock
from core.ecs import WorldECS

from plugins.shared.components.base import *

def move_entities_system(resources: Resources):
    world = resources[WorldECS]
    dt = resources[Clock].get_fixed_delta()
    
    for _, (position, velocity) in world.query_components(Position, Velocity):
        position.apply_vector(velocity.get_velocity() * dt)

    for _, (angle, angle_vel) in world.query_components(Angle, AngleVelocity):
        angle.set_angle(angle.get_angle() + angle_vel.get_velocity() * dt)

def remove_temp_entities_system(resources: Resources):
    world = resources[WorldECS]
    dt = resources[Clock].get_fixed_delta()

    with world.command_buffer() as cmd:
        for ent, temporary in world.query_component(Temporary):
            if temporary.update_and_check(dt):
                cmd.remove_entity(ent)

class BaseSystemsPlugin(Plugin):
    def build(self, app):
        app.add_systems(
            Schedule.FixedUpdate, 
            remove_temp_entities_system,
            move_entities_system,
        )