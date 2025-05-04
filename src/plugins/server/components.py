"""
Server-side components and their behaviour
"""

from core.ecs import WorldECS, component

from plugins.shared.components import *
from plugins.rpcs.server import ControlPlayerCommand

from .actions import ServerActionDispatcher, MoveNetsyncedEntitiesAction
from .session import GameSession

from plugin import Plugin, Resources, Schedule

def syncronize_movables(resources: Resources):
    """
    Syncronize all movable entities by collecting their UIDs, positions and velocities, and sending
    them over
    """

    world = resources[WorldECS]
    action_dispatcher = resources[ServerActionDispatcher]

    moved_entries = []

    for _, (ent, pos, vel) in world.query_components(NetEntity, Position, Velocity, including=NetSyncronized):
        uid = ent.get_uid()

        pos = pos.get_position()
        vel = vel.get_velocity()

        moved_entries.append((
            uid, (pos.x, pos.y), (vel.x, vel.y)
        ))

    action_dispatcher.dispatch_action(MoveNetsyncedEntitiesAction(
        tuple(moved_entries)
    ))

def on_control_player_command(resources: Resources, command: ControlPlayerCommand):
    world = resources[WorldECS]
    uidman = resources[EntityUIDManager]
    session = resources[GameSession]

    player_ent = session.players.get(command.addr)
    if player_ent is None:
        return
    
    pos, vel = world.get_components(player_ent, Position, Velocity)
    pos.set_position(*command.pos)
    vel.set_velocity(*command.vel)

class ServerComponents(Plugin):
    def build(self, app):
        app.add_systems(Schedule.FixedUpdate, syncronize_movables)
        app.add_event_listener(ControlPlayerCommand, on_control_player_command)