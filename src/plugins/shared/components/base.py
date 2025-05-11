import pygame as pg
import numpy as np

from core.ecs import component

@component
class GameEntity:
    """
    A component attached to ALL entities that are part of the game.
    It's sole purpose is to help clean-up all game entities at the end of the game
    """

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

    def get_vector(self) -> pg.Vector2:
        "Return this angle as a directional unit vector"
        return pg.Vector2(np.cos(self.angle), np.sin(self.angle))
    
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
class Team:
    "This component describes from which team an entity comes from. Useful for say, dealing damage"
    def __init__(self, is_enemy: bool):
        self.enemy = is_enemy

    def friend() -> "Team":
        return Team(False)
    
    def enemy() -> "Team":
        return Team(True)

    def is_friendly(self) -> bool:
        return not self.enemy
    
    def is_enemy(self) -> bool:
        return self.enemy
    
    def same_team(self, other: "Team") -> bool:
        return self.enemy == other.enemy

@component
class Health:
    def __init__(self, max_health: float, invincibility: float):
        self.health = max_health
        self.max_health = max_health

        self.invincibility = invincibility
        "The amount of time an entity is immune to damage after taking damage"
        self.on_invincibility = invincibility

    def hurt(self, by: int):
        assert by >= 0, "Can't deal negative damage"

        if self.on_invincibility <= 0:
            self.health = max(self.health-by, 0)
            self.on_invincibility = self.invincibility

    def heal(self, by: int):
        assert by >= 0, "Can't heal by a negative amount"

        self.health = min(self.health+by, self.max_health)

    def get_health(self) -> float:
        return self.health
    
    def set_percentage(self, percentage: float):
        "Set this health to a percentage of the maximum health"

        assert 0 <= percentage <= 1

        self.health = percentage * self.max_health

    def get_percentage(self) -> float:
        "Return the fraction of health to the max health. This can be useful for rendering health bars"
        return self.health/self.max_health
    
    def is_dead(self) -> bool:
        "Returns whether the health is zero"
        return self.health <= 0
    
    def is_invincible(self) -> bool:
        "Check whether this health component can be damaged"
        return self.on_invincibility > 0
    
    def update_invincibility(self, dt: float):
        if self.on_invincibility > 0:
            self.on_invincibility -= dt

@component
class Hittable:
    "A tag component which simply means that an entity can be damaged"
    
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

@component
class Temporary:
    "A component that describes an entity that doesn't live infinitely. Be it "
    def __init__(self, dies_in: float):
        self.dies_in = dies_in

    def update_and_check(self, dt: float) -> bool:
        "Update and check whether the time's up"

        self.dies_in -= dt
        return self.dies_in <= 0
    

@component
class StaticCollider:
    "A static collider is a simple rectangle that doesn't move"
    def __init__(self, w: int, h: int):
        self.rect = pg.Rect(0, 0, w, h)

    def as_moved(self, pos: pg.Vector2) -> "StaticCollider":
        "This method is only used for calculations, colliders usually use positions from components"
        self.rect.topleft = (pos.x, pos.y)
        return self
    
    def get_rect(self) -> pg.Rect:
        return self.rect

@component
class DynCollider:
    "A dynamic, circular collider that's useful for characters. They have mass properties"
    def __init__(self, radius: float, mass: float = 1, sensor: bool = False):
        assert radius > 0, "A collider's radius can't be negative or 0"
        assert mass > 0, "A dynamic collider's mass can't be negative or 0"
        
        self.pos = pg.Vector2(0, 0)
        self._rect = pg.Rect(0, 0, radius*2, radius*2)

        self.radius = radius
        self.mass = mass

        self.sensor = sensor
        "A public attribute. A sensor object doesn't get resolved - it only checks for collisions"

    def as_moved(self, pos: pg.Vector2) -> "DynCollider":
        "This method is only used for calculations, colliders usually use positions from components"
        self.pos = pos
        self._rect.center = (pos.x, pos.y)
        return self
    
    def get_rect(self) -> pg.Rect:
        return self._rect
    
    def is_sensor(self) -> bool:
        return self.sensor
    
    def get_position(self) -> pg.Vector2:
        "Use this to retrieve resolved position vectors"
        return self.pos
        
    def is_colliding_dynamic(self, other: "DynCollider") -> bool:
        "Check if this dynamic collider collides with another dynamic collider"
        return self.pos.distance_squared_to(other.pos) < (self.radius+other.radius)**2
    
    def resolve_collision_dynamic(self, other: "DynCollider"):
        if self.sensor or other.sensor:
            return

        r1, r2 = self.radius, other.radius
        p1, p2 = self.pos, other.pos
        mass1, mass2 = self.mass, other.mass

        mass_sum = mass1+mass2

        distance = p1.distance_to(p2)
        if 0 < distance <= (r1+r2):
            resolution_direction = (p2-p1).normalize()
            move_by = abs((r1+r2)-distance)
            p1 -= resolution_direction * move_by*mass2/mass_sum
            p2 += resolution_direction * move_by*mass1/mass_sum

    def is_colliding_static(self, other: StaticCollider) -> bool:
        rect = other.rect
        pos, radius = self.pos, self.radius

        # Imagine it like a sliding point across our rectangle. If a circle is in the corners - only rectangle's
        # corners can touch with it. Buf if the circle's point is inside the box axis - we can "slide" this
        # point to the closest point to the circle
        point = (
            max(rect.x, min(pos.x, rect.x+rect.w)),
            max(rect.y, min(pos.y, rect.y+rect.h))
        )

        return rect.collidepoint(pos) or pos.distance_to(point) <= radius

    def resolve_collision_static(self, other: StaticCollider):
        if self.sensor:
            return

        rect = other.rect
        pos, radius = self.pos, self.radius

        point = pg.Vector2(
            max(rect.x, min(pos.x, rect.x+rect.w)),
            max(rect.y, min(pos.y, rect.y+rect.h))
        )

        if not rect.collidepoint(pos):
            distance = pos.distance_to(point)
            # This method doesn't resolve collisions inside the box, so this could be a future
            # addition. Hope no one will get stuck (but if they do - they can easily leave)
            if 0 < distance <= radius:
                pos += (pos-point).normalize() * (radius-distance)

@component
class PlayerSpawnpoint:
    """
    A player spawnpoint. Not a gamplay entity, but acts more as a marker for all possible spawnpoints
    on the map. 
    """

@component
class RobberSpawnpoint:
    "The same as `PlayerSpawnpoint` but for robbers"

@component
class DiamondSpawnpoint:
    "The same as `PlayerSpawnpoint` but for diamonds"