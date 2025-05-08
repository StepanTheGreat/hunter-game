from plugins.server.actions import ServerActionDispatcher, CrookifyPolicemanAction

from plugins.shared.components import *
from plugins.shared.entities.characters import *

import random

from .player import PlayerAddress

def make_server_policeman(
    addr: tuple[str, int], 
    uid: int, 
    pos: tuple[float, float]
) -> tuple:
    components = make_policeman(uid, pos) + (PlayerAddress(addr), )
    
    return components

def crookify_random_policeman(resources: Resources):
    """
    A procedure that essentially is going to take a random player, give it robber components,
    and also dispatch appropriate action to notify all other players.
    """

    world = resources[WorldECS]
    dispatcher = resources[ServerActionDispatcher]

    candidates: tuple[tuple[int, NetEntity]] = world.query_component(NetEntity, including=Policeman)

    if len(candidates) == 0:
        # This sure can happen, so in that case we would like to just gracefully close the server
        return

    candidate_ent, net_ent = random.choice(candidates)

    crookify_policeman(world, candidate_ent)

    dispatcher.dispatch_action(CrookifyPolicemanAction(net_ent.get_uid()))
