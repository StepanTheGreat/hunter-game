import pygame as pg

from typing import Union

class StaticCollider:
    "A static collider is a simple rectangle that doesn't move"
    def __init__(self, x: int, y: int, w: int, h: int):
        self.rect = pg.Rect(x, y, w, h)

    def get_rect_ptr(self) -> pg.Rect:
        return self.rect

class DynCollider:
    "A dynamic, circular collider that's useful for characters. They have mass properties"
    def __init__(self, radius: float, pos: tuple[int, int], mass: float = 1, sensor: bool = False):
        assert radius > 0, "A collider's radius can't be negative or 0"
        assert mass > 0, "A dynamic collider's mass can't be negative or 0"
        
        self.pos = pg.Vector2(*pos)
        self.radius = radius
        self.mass = mass
        self.sensor = sensor

    def get_position_ptr(self) -> pg.Vector2:
        """
        The position returned by this method is an object reference. 
        All operations on it will be reflected on the collider as well.
        """
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
            # This method doesn't resolve collisions inside the the box, so this could be a future
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