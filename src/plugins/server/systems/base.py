"""
Server-side components and their behaviour
"""

from core.ecs import WorldECS

from core.time import Clock

from plugins.server.components import *
from plugins.server.actions import *

from plugin import Plugin, Resources, Schedule

def update_invincibilities_system(resources: Resources):
    world = resources[WorldECS]
    dt = resources[Clock].get_fixed_delta()

    for _, health in world.query_component(Health):
        health.update_invincibility(dt)

def remove_dead_entities_system(resources: Resources):
    world = resources[WorldECS]
    
    with world.command_buffer() as cmd:
        for ent, health in world.query_component(Health):
            if health.is_dead():
                cmd.remove_entity(ent)

class BaseSystemsPlugin(Plugin):
    def build(self, app):
        app.add_systems(
            Schedule.FixedUpdate, 
            update_invincibilities_system, 
            remove_dead_entities_system
        )