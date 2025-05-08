from plugin import Plugin, Resources, Schedule

from core.time import Clock
from core.ecs import component, WorldECS

from plugins.shared.components import *

from .characters import Robber

DIAMOND_PICKUP_DISTANCE = 64

@event
class DiamondPickedUpEvent:
    "A diamond was picked up!"
    def __init__(self, ent: int):
        self.ent = ent

@component
class Diamond:
    "A diamond entity tag. Diamonds are picked up by thieves to win the game"

@component
class PickingUp:
    NEEDS_TIME: float = 5

    def __init__(self):
        self.is_picking_up: bool = False
        self.picked_up = PickingUp.NEEDS_TIME

        self.got_picked_up: bool = False

    def tick(self, dt: float):
        "Tick the picking up component"

        if self.got_picked_up:
            return
        
        if self.is_picking_up:
            # If the item is getting picked up, we would like to reduce its lifetime
            self.picked_up -= dt

            # And if 0 - set is as already picked up
            if self.picked_up < 0:
                self.got_picked_up = True
        elif self.picked_up < PickingUp.NEEDS_TIME:
            # If however it's not, we would like to fill its time back
            self.picked_up += dt

    def set_picking_up(self, to: bool):
        "Set this to picking up, thus every tick the item will update"

        self.is_picking_up = to

    def is_picked_up(self) -> bool:
        "Was this item picked up?"

        return self.got_picked_up

def make_diamond(uid: int, pos: tuple[int, int]) -> tuple:
    components = (
        Position(*pos),
        NetEntity(uid),
        PickingUp(),
        Diamond()
    )
    
    return components

def tick_diamonds(resources: Resources):
    "Update all in-game diamonds and if they're getting picked-up - push events"

    world = resources[WorldECS]
    ewriter = resources[EventWriter]
    dt = resources[Clock].get_fixed_delta()

    for ent, picking_up in world.query_component(PickingUp, including=Diamond):
        picking_up.tick(dt)

        if picking_up.is_picked_up():
            ewriter.push_event(DiamondPickedUpEvent(ent))

def pickup_diamonds(resources: Resources):
    "A system that picks up all diamond entities when they're near robbers"

    world = resources[WorldECS]

    robbers = world.query_component(Position, including=Robber)
    diamonds = world.query_components(Position, PickingUp, including=Diamond)

    # So this one is a little bit silly, since we already have colliders and "optimised"
    # collision detection. Well, there's only one robber in a game, so this shouldn't be
    # expensive at all in *these specific circumstances*

    for _, robber_pos in robbers:
        for _, (diamond_pos, picking_up) in diamonds:

            # What this confusing line does is basically saying:
            # if a robber is in a diamond's pick up distance - set it to picking up. In any
            # other case set it to not.
            
            is_picking_up = robber_pos.get_position().distance_to(
                diamond_pos.get_position()
            ) < DIAMOND_PICKUP_DISTANCE

            picking_up.set_picking_up(is_picking_up)

class DiamondPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.FixedUpdate, pickup_diamonds, tick_diamonds)