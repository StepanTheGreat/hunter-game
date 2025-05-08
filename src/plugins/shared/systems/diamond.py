from plugin import Plugin, Resources, Schedule, EventWriter

from core.time import Clock
from core.ecs import WorldECS

from plugins.shared.components import *
from plugins.shared.events.entities import *

DIAMOND_PICKUP_DISTANCE = 64

def tick_diamonds_system(resources: Resources):
    "Update all in-game diamonds and if they're getting picked-up - push events"

    world = resources[WorldECS]
    ewriter = resources[EventWriter]
    dt = resources[Clock].get_fixed_delta()

    for ent, picking_up in world.query_component(PickingUp, including=Diamond):
        picking_up.tick(dt)

        if picking_up.is_picked_up():
            ewriter.push_event(DiamondPickedUpEvent(ent))

def pickup_diamonds_system(resources: Resources):
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

class DiamondSystemsPlugin(Plugin):
    def build(self, app):
        app.add_systems(
            Schedule.FixedUpdate, 
            pickup_diamonds_system, 
            tick_diamonds_system
        )