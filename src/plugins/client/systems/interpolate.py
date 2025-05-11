from plugin import Plugin, Resources, Schedule

from core.time import Clock
from core.ecs import WorldECS

from plugins.client.commands import *
from plugins.client.components import *

from plugins.client.services.session import ServerTime

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

def interpolate_network_components(resources: Resources):
    world = resources[WorldECS]
    server_timer = resources[ServerTime]


    server_time = (server_timer.get_current_time() + server_timer.get_server_offset()) - INTERPOLATION_TIME_DELAY

    # Interpolate positions
    for _, (pos, interpos) in world.query_components(Position, InterpolatedPosition):
        interpos.get_interpolated(server_time)
        pos.set_position(
            *interpos.get_interpolated(server_time)
        )

    # Interpolate angles
    for _, (angle, interangle) in world.query_components(Angle, InterpolatedAngle):
        interangle.get_interpolated(server_time)
        angle.set_angle(interangle.get_interpolated(server_time))

class InterpolationSystemsPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.FixedUpdate, update_render_components, priority=10)
        app.add_systems(
            Schedule.PostUpdate, 
            interpolate_network_components, 
            interpolate_render_components
        )