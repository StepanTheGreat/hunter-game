import pygame as pg

from plugin import Plugin, Schedule, Resources, event, EventWriter

from core.ecs import WorldECS, component

from .components import Position

@component
class StaticCollider:
    "A static collider is a simple rectangle that doesn't move"
    def __init__(self, w: int, h: int):
        self.rect = pg.Rect(0, 0, w, h)

    def as_moved(self, pos: pg.Vector2) -> "StaticCollider":
        "This method is only used for calculations, colliders usually use positions from components"
        self.rect.topleft = (pos.x, pos.y)
        return self

@component
class DynCollider:
    "A dynamic, circular collider that's useful for characters. They have mass properties"
    def __init__(self, radius: float, mass: float = 1, sensor: bool = False):
        assert radius > 0, "A collider's radius can't be negative or 0"
        assert mass > 0, "A dynamic collider's mass can't be negative or 0"
        
        self.pos = pg.Vector2(0, 0)

        self.radius = radius
        self.mass = mass
        self.sensor = sensor

    def as_moved(self, pos: pg.Vector2) -> "DynCollider":
        "This method is only used for calculations, colliders usually use positions from components"
        self.pos = pos
        return self
    
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
        point = pg.Vector2(
            max(rect.x, min(pos.x, rect.x+rect.w)),
            max(rect.y, min(pos.y, rect.y+rect.h))
        )

        return True if rect.collidepoint(point) else pos.distance_squared_to(point) <= radius**2

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

def resolve_collisions(resources: Resources):
    world = resources[WorldECS]
    ewriter = resources[EventWriter]

    # Collect our colliders
    static_colliders = [(ent, collider.as_moved(pos.get_position())) for ent, (pos, collider) in world.query_components(Position, StaticCollider)]
    dyn_colliders = [(ent, (pos, collider.as_moved(pos.get_position()))) for ent, (pos, collider) in world.query_components(Position, DynCollider)]

    for ent1, (_, collider1) in dyn_colliders:
        for ent2, (_, collider2) in dyn_colliders:
            if collider1 == collider2:
                continue
            
            if (collider1.is_sensor() or collider2.is_sensor()):
                if collider1.is_colliding_dynamic(collider2):
                    ewriter.push_event(CollisionEvent(ent1, ent2, DynCollider))
            else:
                collider1.resolve_collision_dynamic(collider2)

    # Now we resolve all static colliders. Again, this is an extremely banal and slow approach
    for ent1, (_, dyn_collider) in dyn_colliders:
        for ent2, stat_collider in static_colliders:
            if dyn_collider.is_sensor():
                if dyn_collider.is_colliding_static(stat_collider):
                    ewriter.push_event(CollisionEvent(ent1, ent2, StaticCollider))
            else:
                dyn_collider.resolve_collision_static(stat_collider)

    for _, (pos, collider) in dyn_colliders:
        pos.set_position(*collider.get_position())

@event
class CollisionEvent:
    """
    Fired whenever a collision between a sensor and an another collider has happened. 
    
    Sensor entity is the entity that listens to said collisions.
    Hit entity is the entity that touched our entity. It's important to note than 2 sensors can absolutely
    collide, so this event will also affect sensor/sensor collisions
    """
    def __init__(self, sensor_entity: int, hit_entity: int, hit_collider_ty: type):
        self.sensor_entity = sensor_entity

        self.hit_entity = hit_entity
        self.hit_collider_ty = hit_collider_ty

class CollisionsPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.FixedUpdate, resolve_collisions, priority=1)