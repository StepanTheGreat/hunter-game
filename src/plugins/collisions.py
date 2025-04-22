import pygame as pg

from plugin import Plugin, Schedule, Resources, event, EventWriter

from core.ecs import WorldECS, component

from collections import deque

from .components import Position

# The less - better, but also more unstable. If a collider's total rectangle is larger than GRID_SIZE*2 - this will get unstable quick
GRID_SIZE = 32

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
        "A public attribute. A sensor object doesn't get resolved - it only checks for collisions"

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

__grid_dynamic: dict[tuple[int, int], list[tuple[int, DynCollider]]] = {}
__grid_static: dict[tuple[int, int], list[tuple[int, StaticCollider]]] = {}
__resolved: set = set()

def resolve_collisions(resources: Resources):
    world = resources[WorldECS]
    ewriter = resources[EventWriter]

    # Collect our colliders
    static_colliders = [(ent, (pos, collider.as_moved(pos.get_position()))) for ent, (pos, collider) in world.query_components(Position, StaticCollider)]
    dyn_colliders = [(ent, (pos, collider.as_moved(pos.get_position()))) for ent, (pos, collider) in world.query_components(Position, DynCollider)]

    events = deque()

    # First, we need to fill up our grids. We divide our grids into 2 types: dynamic and static. 
    # This ugly code will put each collider into its proper grid, based on its position
    for collider_list, collider_grid in ((static_colliders, __grid_static), (dyn_colliders, __grid_dynamic)):

        # Iterate every collider
        for ent, (pos, collider) in collider_list:
            pos = pos.get_position()
            pos = (int(pos.x/GRID_SIZE), int(pos.y/GRID_SIZE))

            to_check_cells = (
                pos, # Current grid
                (pos[0]-1, pos[1]), # Left
                (pos[0]+1, pos[1]),  # Right
                (pos[0], pos[1]+1), # Down 
                (pos[0], pos[1]-1),  # Up

                (pos[0]-1, pos[1]-1), # Top Left
                (pos[0]+1, pos[1]-1),  # Top Right
                (pos[0]-1, pos[1]+1), # Bottom Left 
                (pos[0]-1, pos[1]+1),  # Bottom Right
            )

            # Of course, fill up the grid itself. We will add our collider to ALL neighboring cells
            for cell in to_check_cells:
                if cell not in collider_grid:
                    collider_grid[cell] = [] 
                collider_grid[cell].append((ent, collider))

    # Now, the most ugly part - the collision detection and resolution

    for cell, d_colliders in __grid_dynamic.items():
        # We're going to iterate all cells and its colliders in our dynamic grid

        s_colliders = __grid_static.get(cell, ())
        # As well, we're going to grab static colliders from the same cell if they exist. If not - return an empty tuple

        # Iterate every dynamic collider
        for ent1, collider1 in d_colliders:
            # Iterate again over all colliders
            for ent2, collider2 in d_colliders:

                if collider1 is collider2:
                    # If this is the same collider - just continue iterating
                    continue
                elif ((ent1, ent2) in __resolved) or ((ent2, ent1) in __resolved):
                    # The most important part! Don't resolve or check collisions if pairs are already resolved!
                    continue
                
                # Now, we have different treatment for colliders, depending on if they're sensor or not

                if (collider1.sensor or collider2.sensor) and collider1.is_colliding_dynamic(collider2):
                    # If they are - we only care if they collide

                    # We need to check which of them is sensor and properly reorder for the collision event
                    sensor_ent, hit_ent = (ent1, ent2) if collider1.sensor else (ent2, ent1)

                    # Fire the collision event
                    events.append(CollisionEvent(sensor_ent, hit_ent, DynCollider))
                else:
                    # In any other case - resolve it as a collision between 2 dynamic bodies
                    collider1.resolve_collision_dynamic(collider2)

                # Don't forget to add it to the resolved set of course
                __resolved.add((ent1, ent2))


            # Now, we resolve static collisions!

            for ent2, collider2 in s_colliders:
                if ((ent1, ent2) in __resolved) or ((ent2, ent1) in __resolved):
                    # Of course ignore colliders that we already resolved
                    continue
            
                # The same check applies for sensor and static colliders 

                if collider1.sensor and collider1.is_colliding_static(collider2):
                    events.appendleft(CollisionEvent(ent1, ent2, StaticCollider))
                else:
                    collider1.resolve_collision_static(collider2)

                __resolved.add((ent1, ent2))

    # Now, for simplicity reasons, colliders temporary store their positions for simpler collision resolution
    # We need to move said colliders to their new, resolved positions
    for _, (pos, collider) in dyn_colliders:
        pos.set_position(*collider.get_position())

    # Push all our collected events
    for event in events:
        ewriter.push_event(event)

    # And clear out our grids and sets (well, not really, because we would like to preserve lists and their allocated capacity for performance reasons)
    [cell.clear() for cell in __grid_dynamic.values()]
    [cell.clear() for cell in __grid_static.values()]
    __resolved.clear()

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