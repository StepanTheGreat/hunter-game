import pygame as pg

from plugin import Plugin, Schedule, Resources, EventWriter

from core.ecs import WorldECS, component, ComponentsAddedEvent, ComponentsRemovedEvent

from plugins.shared.events.collisions import *

from collections import deque

from ..components import Position, DynCollider, StaticCollider

from typing import Union

# The less - better, but also more unstable. If a collider's total rectangle is larger than GRID_SIZE*2 - this will get unstable quick
GRID_SIZE = 24

class _CollisionsState:
    """
    A private resource who's purpose is to reduce allocations when performing collision detection.
    For example when filling grids - it makes sense to constantly reallocate lists, as they can keep their
    capacity for other colliders in the future.

    As a bonus, it also acts like cache for all static colliders, so they're not even filled every
    frame.
    """

    def __init__(self):
        self.grid_dynamic: dict[tuple[int, int], list[tuple[int, DynCollider]]] = {}
        "The grid that stores dynamic colliders"

        self.grid_static: dict[tuple[int, int], list[tuple[int, StaticCollider]]] = {}
        "The grid for static colliders. Usually cached"

        self.resolved: set = set()
        "All resolved collider/collider pairs that will be ignored"

    def _clear_grid(self, grid: dict[tuple[int, int], list]):
        for cell in grid.values():
            cell.clear()

    def clear_grid_dynamic(self):
        self._clear_grid(self.grid_dynamic)

    def clear_grid_static(self):
        self._clear_grid(self.grid_static)

    def clear_resolved(self):
        self.resolved.clear()

def fill_grid_with_colliders(
    grid: dict[tuple[int, int], list[tuple[int, DynCollider]]], 
    colliders: tuple[tuple[int, tuple[Position, Union[DynCollider, StaticCollider]]]]
):
    """
    Fill a grid with provided colliders. This procedure doesn't clear anything, so it's your responsibility
    to do so.
    """

    gsize = GRID_SIZE

    # Idk, but I think I gain like 0.1% boost when not recreating these values for every cell
    main_cross_indices = (0, 1, 2, 3) 
    
    # Iterate every collider
    for ent, (pos, collider) in colliders:
        pos = pos.get_position()
        pos = (int(pos.x/GRID_SIZE), int(pos.y/GRID_SIZE))
        collider_rect = collider.get_rect()

        # So what is this confusing algorithm, why am I reusing simple lists and so on?
        # For the first case I can't really respond, as I believe it gives me some hope that the
        # algorithm will allocate less and thus become a bit faster, though I think the performance
        # difference will be less than 0.1%
        #
        # Anyway, to our algorithm! Because it doesn't make sense to simply add our collider to every
        # single cell around it - we would like to only add it to cells that it touches. For this reason
        # our colliders have a method `get_rect`, which computes their bounding box.
        # Now, if you imagine 8 cells, around 1 cell (9 in total), you would see something like this:
        # 
        # o -- # -- o
        # |    |    |
        # # -- @ -- #
        # |    |    |
        # 0 -- # -- o
        #
        # We got the center, the cross and the corners. So, 9 cells in total.
        #
        # We automatically add to the main cell, as it will always have our collider.
        # But regarding our other 8 cells... we don't need to check EVERY cell for collisions...
        # Because corners are in between 2 cross cells and our center cell - it's absolutely impossible
        # for our collider to somehow not collide with any of the 2 cross cells.
        # What this allows us to do, is to only check for 4 cell collisions (left, top, right, bottom),
        # and for every pair, if both are true - add their corner. For example, if left and top
        # are true - top-left cell can be used as well
        # 
        # This in turn results in complexity N4, which is still a lot, but more managable overall. 
        
        # Define our 8 surrounding cells. Ignore the slicing, it just makes me feel safer... Safer?
        cross_cells = (
            (pos[0]-1, pos[1]),   # Left
            (pos[0]-1, pos[1]-1), # Top-Left 
            (pos[0],   pos[1]-1), # Top
            (pos[0]+1, pos[1]-1), # Top-right
            (pos[0]+1, pos[1]),   # Right
            (pos[0]+1, pos[1]+1), # Bottom-Right
            (pos[0],   pos[1]+1), # Bottom
            (pos[0]-1, pos[1]+1), # Bottom-Left
        )

        # Check rect collisions for every cross cell, and return a tuple of booleans:
        # (left, top, right, bottom)
        main_cross_cells = tuple(
            collider_rect.colliderect(x*gsize, y*gsize, gsize, gsize)
            for (x, y) in cross_cells[::2]
        )

        # Now, we're going to collision results for our 4 main cells
        for ind in main_cross_indices:
            if main_cross_cells[ind]:
                # If it has collided - add the collider to the cells
                local_ind = ind*2
                grid.setdefault(cross_cells[local_ind], []).append((ent, collider))

                # AND, if the cell before this one also has a collision - add the collider to the 
                # cell in between (corner)
                if main_cross_cells[ind-1]:
                    grid.setdefault(cross_cells[local_ind-1], []).append((ent, collider))
        
        # Finally, add our primary cell to the colliders
        grid.setdefault(pos, []).append((ent, collider))

def resolve_collisions_system(resources: Resources):
    world = resources[WorldECS]
    ewriter = resources[EventWriter]

    collisions_state = resources[_CollisionsState]

    grid_dynamic = collisions_state.grid_dynamic
    grid_static = collisions_state.grid_static
    resolved = collisions_state.resolved


    # Collect our colliders
    dyn_colliders = [(ent, (pos, collider.as_moved(pos.get_position()))) for ent, (pos, collider) in world.query_components(Position, DynCollider)]
    fill_grid_with_colliders(grid_dynamic, dyn_colliders)

    events = deque()

    # Now, the most ugly part - the collision detection and resolution
    checks = 0
    for cell, d_colliders in grid_dynamic.items():
        # We're going to iterate all cells and its colliders in our dynamic grid

        s_colliders = grid_static.get(cell, ())
        # As well, we're going to grab static colliders from the same cell if they exist. If not - return an empty tuple

        # Iterate every dynamic collider
        for ent1, collider1 in d_colliders:
            
            # Resolve dynamic collisions
            for ent2, collider2 in s_colliders:
                checks += 1
                if ((ent1, ent2) in resolved) or ((ent2, ent1) in resolved):
                    # Of course ignore colliders that we already resolved
                    continue
            
                # The same check applies for sensor and static colliders 

                if collider1.sensor and collider1.is_colliding_static(collider2):
                    events.appendleft(CollisionEvent(ent1, ent2, StaticCollider))
                else:
                    collider1.resolve_collision_static(collider2)

                resolved.add((ent1, ent2))

            # Resolve static collisions
            for ent2, collider2 in d_colliders:
                checks += 1
                if collider1 is collider2:
                    # If this is the same collider - just continue iterating
                    continue
                elif ((ent1, ent2) in resolved) or ((ent2, ent1) in resolved):
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
                resolved.add((ent1, ent2))

    # Now, for simplicity reasons, colliders temporary store their positions for simpler collision resolution
    # We need to move said colliders to their new, resolved positions
    for _, (pos, collider) in dyn_colliders:
        pos.set_position(*collider.get_position())

    # Push all our collected events
    for event in events:
        ewriter.push_event(event)

    # Clear our state (but not entirely)
    collisions_state.clear_grid_dynamic()
    collisions_state.clear_resolved()

def on_new_static_collider(resources: Resources, event: Union[ComponentsRemovedEvent, ComponentsAddedEvent]):
    world = resources[WorldECS]
    collisions_state = resources[_CollisionsState]

    if StaticCollider not in event.components:
        return    

    collisions_state.clear_grid_static()
    # We will need to clear out our previous static grid cache

    static_colliders = [(ent, (pos, collider.as_moved(pos.get_position()))) for ent, (pos, collider) in world.query_components(Position, StaticCollider)]

    fill_grid_with_colliders(collisions_state.grid_static, static_colliders)

class CollisionsPlugin(Plugin):
    def build(self, app):
        app.insert_resource(_CollisionsState())

        app.add_systems(Schedule.FixedUpdate, resolve_collisions_system, priority=1)

        app.add_event_listener(ComponentsAddedEvent, on_new_static_collider)
        app.add_event_listener(ComponentsRemovedEvent, on_new_static_collider)