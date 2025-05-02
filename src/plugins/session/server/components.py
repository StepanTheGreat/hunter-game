"""
Server-side components and their behaviour
"""

from core.ecs import WorldECS, component, ComponentsRemovedEvent

from plugins.network import only_server, Server
from plugins.components import Position, Velocity
from plugins.session.client.rpcs import *

from ..components import NetEntity, NetSyncronized
from ..pack import pack_velocity

from plugin import Plugin, Resources, Schedule

import numpy as np

@only_server
def syncronize_movables(resources: Resources):
    """
    Syncronize all movable entities by updating their velocity/position every frame across the
    network
    """

    world = resources[WorldECS]
    server = resources[Server]

    movables_packet = bytes()
    packed_entities = 0

    for _, (ent, pos, vel) in world.query_components(NetEntity, Position, Velocity, including=NetSyncronized):
        uid = ent.get_uid()

        pos = pos.get_position()
        vel = vel.get_velocity()

        vel_angle, vel_length = pack_velocity(vel.x, vel.y)

        movables_packet += MOVABLE_STRUCT_FORMAT.pack(
            uid,
            int(pos.x), int(pos.y),
            vel_angle, vel_length
        )

    # This line should be removed in the future, as 127 entities is unlikely to ever get reached
    assert packed_entities <= MOVABLE_ENTITIES_LIMIT, "Reached movable entity limit"

    # Now we can call the RPC!
    server.call_all(move_netsynced_entities, movables_packet)