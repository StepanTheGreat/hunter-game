from plugin import Plugin, Resources, Schedule

from core.ecs import WorldECS

from modules.inteprolation import Interpolated, InterpolatedAngle

from plugins.rpcs.client import *
from plugins.shared.components import *

from plugins.shared.entities.player import MainPlayer

@component
class RenderPosition:
    def __init__(self, height: float):
        self.height = height

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

def on_move_netsynced_entities_command(resources: Resources, command: MoveNetsyncedEntitiesCommand):
    "Apply net syncronization on all requested network entities"

    world = resources[WorldECS]
    uidman = resources[EntityUIDManager]

    for (uid, new_pos, new_vel) in command.entries:
        ent = uidman.get_ent(uid)
        if ent is None:
            continue
        elif world.has_component(ent, MainPlayer):
            continue
            
        pos, vel = world.get_components(ent, Position, Velocity)
        pos.set_position(*new_pos)
        vel.set_velocity(*new_vel)

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
        app.add_systems(Schedule.PostUpdate, interpolate_render_components)

        app.add_event_listener(MoveNetsyncedEntitiesCommand, on_move_netsynced_entities_command)
        app.add_event_listener(KillEntityCommand, on_kill_entity_command)