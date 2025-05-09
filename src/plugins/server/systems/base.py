"""
Server-side components and their behaviour
"""

from core.ecs import WorldECS

from core.time import Clock, schedule_systems_seconds 

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

def sync_players_system(resources: Resources):
    """
    Syncronize all movable entities by collecting their UIDs, positions, angles and shooting statuses,
    sending them over network
    """

    world = resources[WorldECS]
    action_dispatcher = resources[ServerActionDispatcher]

    moved_entries = []

    for _, (ent, pos, angle, controller) in world.query_components(NetEntity, Position, Angle, PlayerController, including=NetSyncronized):
        uid = ent.get_uid()

        pos = pos.get_position()
        angle = angle.get_angle()
        is_shooting = controller.is_shooting

        moved_entries.append((uid, (pos.x, pos.y), angle, is_shooting))

    action_dispatcher.dispatch_action(SyncPlayersAction(
        tuple(moved_entries)
    ))

class BaseSystemsPlugin(Plugin):
    def build(self, app):
        app.add_systems(
            Schedule.FixedUpdate, 
            update_invincibilities_system, 
            remove_dead_entities_system
        )

        # We would like to syncronize our movables 20 times a second
        schedule_systems_seconds(app, (sync_players_system, 1/20, True))