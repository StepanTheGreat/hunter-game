from plugin import Plugin, Resources

from core.ecs import WorldECS

from plugins.server.actions import ServerActionDispatcher, CrookifyPolicemanAction
from plugins.server.components import *
from plugins.server.commands import CrookifyRandomPlayerCommand

# TODO: Remove this things
from plugins.shared.entities.characters import crookify_policeman

import random

def on_crookify_player_command(resources: Resources):
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

    # TODO: Remove this thing
    crookify_policeman(world, candidate_ent)

    dispatcher.dispatch_action(CrookifyPolicemanAction(net_ent.get_uid()))

class CharactersHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(CrookifyRandomPlayerCommand, on_crookify_player_command)