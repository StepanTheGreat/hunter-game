"""
Server-side components and their behaviour
"""

from core.ecs import WorldECS

from core.time import schedule_systems_seconds 

from plugins.shared.components import *
from plugins.rpcs.server import ControlPlayerCommand

from .actions import *
from .session.session import GameSession

from plugin import Plugin, Resources, Schedule

def syncronize_movables(resources: Resources):
    """
    Syncronize all movable entities by collecting their UIDs, positions and velocities, and sending
    them over
    """

    world = resources[WorldECS]
    action_dispatcher = resources[ServerActionDispatcher]

    moved_entries = []

    for _, (ent, pos) in world.query_components(NetEntity, Position, including=NetSyncronized):
        uid = ent.get_uid()

        pos = pos.get_position()

        moved_entries.append((uid, (pos.x, pos.y)))

    action_dispatcher.dispatch_action(MoveNetsyncedEntitiesAction(
        tuple(moved_entries)
    ))

def on_control_player_command(resources: Resources, command: ControlPlayerCommand):
    world = resources[WorldECS]
    session = resources[GameSession]

    player_ent = session.players.get(command.addr)
    if player_ent is None:
        return
    
    pos, vel = world.get_components(player_ent, Position, Velocity)
    pos.set_position(*command.pos)
    vel.set_velocity(*command.vel)

def on_network_entity_removal(resources: Resources, event: RemovedNetworkEntity):
    """
    When a network entity gets removed from the ECS world, we would like to push an
    action notifying all other clients of this removal.
    """

    action = resources[ServerActionDispatcher]
    
    action.dispatch_action(KillEntityAction(event.uid))

class ServerComponents(Plugin):
    def build(self, app):
        app.add_event_listener(ControlPlayerCommand, on_control_player_command)
        app.add_event_listener(RemovedNetworkEntity, on_network_entity_removal)

        # We would like to syncronize our movables 20 times a second
        schedule_systems_seconds(app, (syncronize_movables, 1/20, True))