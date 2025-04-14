import pygame as pg
from typing import Union

from plugin import Plugin, Schedule, Resources

from core.ecs import WorldECS

from .components import Position

class StaticCollider:
    "A static collider is a simple rectangle that doesn't move"
    def __init__(self, w: int, h: int):
        self.rect = pg.Rect(0, 0, w, h)

    def as_moved(self, pos: pg.Vector2) -> "StaticCollider":
        "This method is only used for calculations, colliders usually use positions from components"
        self.rect.topleft = (pos.x, pos.y)
        return self

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

class CollisionManager:
    def __init__(self):
        self.static_colliders: list[StaticCollider] = []
        self.dynamic_colliders: list[DynCollider] = []

    def __get_collider_storage(self, ty: object) -> list:
        if type(ty) == DynCollider:
            return self.dynamic_colliders
        elif type(ty) == StaticCollider:
            return self.static_colliders
        
    def add_collider(self, collider: Union[DynCollider, StaticCollider]):
        storage = self.__get_collider_storage(collider)
        storage.append(collider)

    def remove_collider(self, collider: Union[DynCollider, StaticCollider]):
        storage = self.__get_collider_storage(collider)
        storage.remove(collider)
        # This is a slow removal operation, could be replaced with a swap in the future

    def __contains__(self, collider: Union[DynCollider, StaticCollider]):
        storage = self.__get_collider_storage(collider)
        return collider in storage

    def resolve_collisions(self):
        "This method doesn't take any arguments and can be called multiple times for better resolution quality"
        # First we need to resolve dynamic-dynamic collisions

        # This is a stupid solution. The collision manager should use grids instead in the future
        for collider1 in self.dynamic_colliders:
            for collider2 in self.dynamic_colliders:
                if collider1 == collider2:
                    continue

                collider1.resolve_collision_dynamic(collider2)

        # Now we resolve all static colliders. Again, this is an extremely banal and slow approach
        for dyn_collider in self.dynamic_colliders:
            for stat_collider in self.static_colliders:
                dyn_collider.resolve_collision_static(stat_collider)

    def clear(self):
        "Remove all colliders from this world (static and dynamic)"
        self.static_colliders.clear()
        self.dynamic_colliders.clear()

    def update(self, fixed_delta: float):
        "Move all colliders and resolve their collisions"

        # First we move all colliders
        for collider in self.dynamic_colliders:
            collider.update_position(fixed_delta)
        
        # Then we resolve their collisions
        self.resolve_collisions()

# def update_collisions(resources: Resources):
#     fixed_delta = resources[Clock].get_fixed_delta()

#     resources[CollisionManager].update(fixed_delta)

#     for ent, (position, collider) in resources[WorldECS].query_components(Position, DynCollider):
#         position.set_position(*collider.get_position())

def resolve_collisions(resources: Resources):
    # return
    world = resources[WorldECS]

    # Collect our colliders
    static_colliders = [collider.as_moved(pos.get_position()) for _, (pos, collider) in world.query_components(Position, StaticCollider)]
    dyn_colliders = [(pos, collider.as_moved(pos.get_position())) for _, (pos, collider) in world.query_components(Position, DynCollider)]

    for _, collider1 in dyn_colliders:
        for _, collider2 in dyn_colliders:
            if collider1 != collider2:
                collider1.resolve_collision_dynamic(collider2)

    # Now we resolve all static colliders. Again, this is an extremely banal and slow approach
    for dyn_collider in dyn_colliders:
        for stat_collider in static_colliders:
            dyn_collider.resolve_collision_static(stat_collider)

    for pos, collider in dyn_colliders:
        pos.set_position(*collider.get_position())

# def apply_colider_velocities(resources: Resources):
#     """
#     An entity can change its velocity via Velocity component. 
#     Here we will do exactly that, before we can proceed to actually update the simulation
#     """

#     for ent, (velocity, collider) in resources[WorldECS].query_components(Velocity, DynCollider):
#         collider.set_velocity(velocity.get_velocity())
    
# We will make our DynCollider a component.
# When an entity attaches a DynCollider component - we will listen for the ComponentsAddedEvent, and 
# register said collider to our CollisionManager automatically.

# def on_collider_added(resources: Resources, event: ComponentsAddedEvent):
#     if DynCollider in event.components:
#         resources[CollisionManager].add_collider(event.components[DynCollider])

# def on_collider_removed(resources: Resources, event: ComponentsRemovedEvent):
#     if DynCollider in event.components:
#         resources[CollisionManager].remove_collider(event.components[DynCollider])

class CollisionsPlugin(Plugin):
    def build(self, app):
        app.insert_resource(CollisionManager())
        # app.add_systems(Schedule.FixedUpdate, apply_colider_velocities, update_collisions)
        app.add_systems(Schedule.FixedUpdate, resolve_collisions, priority=1)

        # app.add_event_listener(ComponentsAddedEvent, on_collider_added)
        # app.add_event_listener(ComponentsRemovedEvent, on_collider_removed)