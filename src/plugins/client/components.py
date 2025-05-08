from plugin import Plugin, Resources, Schedule

from core.ecs import WorldECS

from modules.inteprolation import Interpolated, InterpolatedAngle

from plugins.rpcs.client import *
from plugins.shared.components import *

<<<<<<< HEAD
from plugins.shared.entities.player import MainPlayer

@component
class RenderPosition:
    def __init__(self, height: float):
        self.height = height

=======
from plugins.client.session import ServerTime

from plugins.shared.entities.player import MainPlayer

INTERPOLATION_TIME_DELAY = 0.05
"""
This is the time we're going to subtract when interpolating network positions. Why?
Because it will make our clients move like they're in the past. Ideally we would like to live in
the past, so that all motion doesn't seem to immediate for us.

We have to play with this constant to see what works best
"""

@component
class RenderPosition:
    def __init__(self):
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
        self.positions = Interpolated(pg.Vector2(0, 0))
        self.interpolated = self.positions.get_value()

    def set_position(self, x: float, y: float):
        self.positions.push_value(pg.Vector2(x, y))

    def interpolate(self, alpha: float):
        self.interpolated = self.positions.get_interpolated(alpha)

    def get_position(self) -> pg.Vector2:
        return self.interpolated

@component
class RenderAngle:
    def __init__(self):
        self.angles = InterpolatedAngle(0)
        self.interpolated = self.angles.get_value()

    def interpolate(self, alpha: float):
        self.interpolated = self.angles.get_interpolated(alpha)

    def set_angle(self, new_angle: float):
        self.angles.push_value(new_angle)

    def get_angle(self) -> float:
        return self.interpolated    
    
    def get_vector(self) -> pg.Vector2:
        "Return this angle as a directional unit vector"
        return pg.Vector2(np.cos(self.interpolated), np.sin(self.interpolated))

<<<<<<< HEAD
=======
@component
class InterpolatedPosition:
    """
    Because movement packets itroduce inherent jitter (as they can be delayed, they're sent way less
    frequently than the refresh rate or so on), this component is going to fix the problem by
    interpolating positions. Double interpolation right here! Essentially, when receiving movement
    packets - they should go directly to this component instead, which is going to interpolate entities.
    
    This component however shouldn't be applied to the client, as it controls their own movement
    without much jitter.
    """
    def __init__(self):
        self.interpolated = Interpolated(pg.Vector2(0, 0))

        self.time: tuple[float, float] = (0, 0)
        "The time used when interpolating. It gets swapped every time a new position gets introduced."

    def push_position(self, time: float, new_x: float, new_y: float):
        self.interpolated.push_value(pg.Vector2(new_x, new_y))
        self.time = (self.time[-1], time)

    def get_interpolated(self, current_time: float) -> pg.Vector2:
        prelast, last = self.time

        # We're computing the alpha here of our current time. Essentially, if we have 2 points in time
        # A and B, and we have time C in between these time points, we would like to get a value
        # between 0 and 1, which we could then use as alpha for our position interpolation.
        #
        # For this we first need to get the delta time between our current time and A (the oldest point).
        # Then, we're dividing this by the delta time between A and B.
        # So if for example A is 1, B is 2 and C is 1.5, then the formula will be:
        # (C-A)/(B-A) -> (1.5-1)/(2-1) -> 0.5/1 -> 0.5
        alpha = min(
            1, 
            max((current_time-prelast)/(last-prelast+0.0001), 0)
        )

        return self.interpolated.get_interpolated(alpha)

>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
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

<<<<<<< HEAD
def on_move_netsynced_entities_command(resources: Resources, command: MoveNetsyncedEntitiesCommand):
    "Apply net syncronization on all requested network entities"

    world = resources[WorldECS]
    uidman = resources[EntityUIDManager]

    for (uid, new_pos, new_vel) in command.entries:
=======
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
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
        ent = uidman.get_ent(uid)
        if ent is None:
            continue
        elif world.has_component(ent, MainPlayer):
            continue
<<<<<<< HEAD
            
        pos, vel = world.get_components(ent, Position, Velocity)
        pos.set_position(*new_pos)
        vel.set_velocity(*new_vel)
=======
        elif not world.has_component(ent,  InterpolatedPosition):
            continue

        pos = world.get_component(ent, InterpolatedPosition)
        pos.push_position(server_time, *new_pos)
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75

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
<<<<<<< HEAD
        app.add_systems(Schedule.PostUpdate, interpolate_render_components)

        app.add_event_listener(MoveNetsyncedEntitiesCommand, on_move_netsynced_entities_command)
=======
        app.add_systems(
            Schedule.PostUpdate, 
            interpolate_network_positions, 
            interpolate_render_components
        )

        app.add_event_listener(MovePlayersCommand, on_move_players_command)
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
        app.add_event_listener(KillEntityCommand, on_kill_entity_command)