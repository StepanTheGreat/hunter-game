"""
Server-side components and their behaviour
"""

<<<<<<< HEAD
from core.ecs import WorldECS, component

from plugins.shared.components import *
from plugins.rpcs.server import ControlPlayerCommand

from .actions import *
from .session import GameSession

from plugin import Plugin, Resources, Schedule

def syncronize_movables(resources: Resources):
=======
from core.ecs import WorldECS

from core.time import schedule_systems_seconds 

from plugins.shared.components import *
from plugins.shared.entities.player import PlayerController
from plugins.rpcs.server import ControlPlayerCommand

from .actions import *
from .session.session import GameSession

from plugin import Plugin, Resources, Schedule

def update_invincibilities(resources: Resources):
    world = resources[WorldECS]
    dt = resources[Clock].get_fixed_delta()

    for ent, health in world.query_component(Health):
        health.update_invincibility(dt)

def remove_dead_entities(resources: Resources):
    world = resources[WorldECS]
    
    with world.command_buffer() as cmd:
        for ent, health in world.query_component(Health):
            if health.is_dead():
                cmd.remove_entity(ent)

def move_players(resources: Resources):
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
    """
    Syncronize all movable entities by collecting their UIDs, positions and velocities, and sending
    them over
    """

    world = resources[WorldECS]
    action_dispatcher = resources[ServerActionDispatcher]

    moved_entries = []

<<<<<<< HEAD
    for _, (ent, pos, vel) in world.query_components(NetEntity, Position, Velocity, including=NetSyncronized):
        uid = ent.get_uid()

        pos = pos.get_position()
        vel = vel.get_velocity()

        moved_entries.append((
            uid, (pos.x, pos.y), (vel.x, vel.y)
        ))

    action_dispatcher.dispatch_action(MoveNetsyncedEntitiesAction(
=======
    for _, (ent, pos) in world.query_components(NetEntity, Position, including=NetSyncronized):
        uid = ent.get_uid()

        pos = pos.get_position()

        moved_entries.append((uid, (pos.x, pos.y)))

    action_dispatcher.dispatch_action(MovePlayersAction(
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
        tuple(moved_entries)
    ))

def on_control_player_command(resources: Resources, command: ControlPlayerCommand):
    world = resources[WorldECS]
<<<<<<< HEAD
    uidman = resources[EntityUIDManager]
=======
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
    session = resources[GameSession]

    player_ent = session.players.get(command.addr)
    if player_ent is None:
        return
<<<<<<< HEAD
    
    pos, vel = world.get_components(player_ent, Position, Velocity)
    pos.set_position(*command.pos)
    vel.set_velocity(*command.vel)
=======
    elif not world.contains_entity(player_ent):
        # An entity might as well just die in this exact moment
        return
    
    pos, vel, angle, angle_vel, controller = world.get_components(
        player_ent, 
        Position, 
        Velocity, 
        Angle, 
        AngleVelocity,
        PlayerController
    )
    pos.set_position(*command.pos)
    vel.set_velocity(*command.vel)
    angle.set_angle(command.angle)
    angle_vel.set_velocity(command.angle_vel)

    controller.is_shooting = command.is_shooting
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75

def on_network_entity_removal(resources: Resources, event: RemovedNetworkEntity):
    """
    When a network entity gets removed from the ECS world, we would like to push an
    action notifying all other clients of this removal.
    """
<<<<<<< HEAD

    action = resources[ServerActionDispatcher]
=======
    session = resources[GameSession]
    action = resources[ServerActionDispatcher]

    # If this is a player, we would like to replace its entity with `None`
    for player_addr, ent in session.players:
        if ent == event.ent:
            session.players[player_addr] = None
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
    
    action.dispatch_action(KillEntityAction(event.uid))

class ServerComponents(Plugin):
    def build(self, app):
<<<<<<< HEAD
        app.add_systems(Schedule.FixedUpdate, syncronize_movables)
        app.add_event_listener(ControlPlayerCommand, on_control_player_command)
        app.add_event_listener(RemovedNetworkEntity, on_network_entity_removal)
=======
        app.add_systems(
            Schedule.FixedUpdate, 
            update_invincibilities, 
            remove_dead_entities
        )

        app.add_event_listener(ControlPlayerCommand, on_control_player_command)
        app.add_event_listener(RemovedNetworkEntity, on_network_entity_removal)

        # We would like to syncronize our movables 20 times a second
        schedule_systems_seconds(app, (move_players, 1/20, True))
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
