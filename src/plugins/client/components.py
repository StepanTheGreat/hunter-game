from plugin import Plugin, Resources, Schedule

from core.ecs import WorldECS

from plugins.rpcs.client import *
from plugins.client.components import *

from plugins.client.session import ServerTime

from plugins.shared.entities.player import MainPlayer

INTERPOLATION_TIME_DELAY = 0.05
"""
This is the time we're going to subtract when interpolating network positions. Why?
Because it will make our clients move like they're in the past. Ideally we would like to live in
the past, so that all motion doesn't seem to immediate for us.

We have to play with this constant to see what works best
"""


def update_render_components(resources: Resources):
    world = resources[WorldECS]
    
    # We will update and then interpolate positions and angles

    for _, (render_pos, pos) in world.query_components(RenderPosition, Position):
        render_pos.set_position(*pos.get_position())

    for _, (render_angle, angle) in world.query_components(RenderAngle, Angle):
        render_angle.set_angle(angle.get_angle())

def interpolate_render_components(resources: Resources):
    """
    For rendering purposes, our components must be interpolated before rendering 
    (since our physics world is inherently separate from the render world).
    """
    world = resources[WorldECS]
    alpha = resources[Clock].get_alpha()
    
    # We will update and then interpolate positions and angles

    for interpolatable in (RenderPosition, RenderAngle):
        for _, component in world.query_component(interpolatable):
            component.interpolate(alpha)

def interpolate_network_positions(resources: Resources):
    world = resources[WorldECS]
    server_time = resources[ServerTime].get_current_time() - INTERPOLATION_TIME_DELAY

    for _, (pos, interpos) in world.query_components(Position, InterpolatedPosition):
        interpos.get_interpolated(server_time)
        pos.set_position(
            *interpos.get_interpolated(server_time)
        )

def on_move_players_command(resources: Resources, command: MovePlayersCommand):
    "Apply net syncronization on all requested players"

    world = resources[WorldECS]
    uidman = resources[EntityUIDManager]
    server_time = resources[ServerTime].get_current_time()

    for (uid, new_pos) in command.entries:
        ent = uidman.get_ent(uid)
        if ent is None:
            continue
        elif world.has_component(ent, MainPlayer):
            continue
        elif not world.has_component(ent,  InterpolatedPosition):
            continue

        pos = world.get_component(ent, InterpolatedPosition)
        pos.push_position(server_time, *new_pos)

def on_kill_entity_command(resources: Resources, command: KillEntityCommand):
    "When we receive an entity kill command from the server - we should kill said entity"

    world = resources[WorldECS]
    uidman = resources[EntityUIDManager]

    target_uid = command.uid
    target_ent = uidman.get_ent(target_uid)

    if target_ent is not None and world.contains_entity(target_ent):
        with world.command_buffer() as cmd:
            cmd.remove_entity(target_ent)

class ClientCommonComponentsPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.FixedUpdate, update_render_components, priority=10)
        app.add_systems(
            Schedule.PostUpdate, 
            interpolate_network_positions, 
            interpolate_render_components
        )

        app.add_event_listener(MovePlayersCommand, on_move_players_command)
        app.add_event_listener(KillEntityCommand, on_kill_entity_command)