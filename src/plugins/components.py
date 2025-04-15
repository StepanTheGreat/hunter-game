import pygame as pg
import numpy as np

from plugin import Plugin, Schedule, Resources

from core.pg import Clock
from core.ecs import WorldECS, component

from modules.inteprolation import Interpolated, InterpolatedAngle

@component
class Position:
    "An entity position. If added with Collider component - it will also get automatically overwritten by Collider's interpolated position"
    def __init__(self, x: float, y: float):
        self.position = pg.Vector2(x, y)

    def apply_vector(self, vec: pg.Vector2):
        "Add the provided vector to the current position vector"
        self.position += vec

    def set_position(self, x: float, y: float):
        self.position.x, self.position.y = x, y

    def get_position(self) -> pg.Vector2:
        return self.position.copy()
        
@component
class RenderPosition:
    def __init__(self, x: float, y: float, height: float):
        self.height = height

        self.positions = Interpolated(pg.Vector2(x, y))
        self.interpolated = self.positions.get_value()

    def set_position(self, x: float, y: float):
        self.positions.push_value(pg.Vector2(x, y))

    def interpolate(self, alpha: float):
        self.interpolated = self.positions.get_interpolated(alpha)

    def get_position(self) -> pg.Vector2:
        return self.interpolated

@component
class Angle:
    "The direction the entity is facing"
    def __init__(self, angle: float):
        self.angle = angle

    def set_angle(self, new_angle: float):
        if new_angle > np.pi:
            new_angle = -np.pi
        elif new_angle < -np.pi:
            new_angle = np.pi
            
        self.angle = new_angle

    def get_angle(self) -> float:
        return self.angle

@component
class RenderAngle:
    def __init__(self, initial: float):
        self.angles = InterpolatedAngle(initial)
        self.interpolated = self.angles.get_value()

    def interpolate(self, alpha: float):
        self.interpolated = self.angles.get_interpolated(alpha)

    def set_angle(self, new_angle: float):
        self.angles.push_value(new_angle)

    def get_angle(self) -> float:
        return self.interpolated    
    
@component
class Velocity:
    "Entity's directional velocity. Used with dynamic colliders to update said entity's velocity"
    def __init__(self, x: float, y: float, speed: float):
        self.vel = pg.Vector2(x, y)
        self.speed = speed

    def set_velocity(self, x: float, y: float):
        self.vel.x, self.vel.y = x, y

    def get_velocity(self) -> pg.Vector2:
        "Returns the velocity vector multiplied by the internal speed scalar"
        return self.vel * self.speed

@component
class AngleVelocity:
    def __init__(self, vel: float, speed: float):
        self.vel = vel
        self.speed = speed

    def set_velocity(self, new_vel: float):
        self.vel = new_vel

    def get_velocity(self) -> float:
        return self.vel * self.speed 

@component
class Health:
    def __init__(self, max_health: float):
        self.health = max_health
        self.max_health = max_health

    def hurt(self, by: int):
        assert by >= 0, "Can't deal negative damage"

        self.health = max(self.health-by, 0)

    def heal(self, by: int):
        assert by >= 0, "Can't heal by a negative amount"

        self.health = min(self.health+by, self.max_health)

    def get_health(self) -> float:
        return self.health

    def get_percentage(self) -> float:
        "Return the fraction of health to the max health. This can be useful for rendering health bars"
        return self.health/self.max_health
    
    def is_dead(self) -> bool:
        "Returns whether the health is zero"
        return self.health <= 0
    
@component
class Timer:
    "A general purpose timer, be it for cooldowns or any other stuff"
    def __init__(self, duration: float, current_duration: float = 0):
        self.duration = duration
        self.current_duration = current_duration

    def update(self, dt: float):
        if self.current_duration > 0:
            self.current_duration -= dt

    def has_finished(self) -> bool:
        return self.current_duration <= 0

    def reset(self):
        "Reset this timer back to its duration"
        self.current_duration = self.duration

def move_entities(resources: Resources):
    world = resources[WorldECS]
    dt = resources[Clock].get_fixed_delta()
    
    for ent, (position, velocity) in world.query_components(Position, Velocity):
        position.apply_vector(velocity.get_velocity() * dt)

    for ent, (angle, angle_vel) in world.query_components(Angle, AngleVelocity):
        angle.set_angle(angle.get_angle() + angle_vel.get_velocity() * dt)

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

class CommonComponentsPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.FixedUpdate, move_entities)
        app.add_systems(Schedule.FixedUpdate, update_render_components, priority=10)
        app.add_systems(Schedule.PostUpdate, interpolate_render_components)