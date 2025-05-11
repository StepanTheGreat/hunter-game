from plugin import Plugin, Resources

from core.ecs import WorldECS
from core.events import ComponentsRemovedEvent

from plugins.server.events import GameStartedEvent
from plugins.server.actions import ServerActionDispatcher, CrookifyPolicemanAction
from plugins.server.components import *

# TODO: Remove this things
from plugins.shared.entities.characters import crookify_policeman
from plugins.server.services.state import CurrentGameState, GameState

import random

def on_game_started(resources: Resources, _):
    """
    A procedure that essentially is going to take a random player, give it robber components,
    and also dispatch appropriate action to notify all other players.

    Then, we will move all our players to new, random locations
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


    player_spawnpoints = world.query_component(Position, including=PlayerSpawnpoint)
    robber_spawnpoints = world.query_component(Position, including=RobberSpawnpoint)

    assert len(robber_spawnpoints) > 0, "No robber spawnpoints available"
    assert len(player_spawnpoints) > 0, "No player spawnpoints available"
    
    for _, player_pos in world.query_component(Position, including=Policeman):
        spawnpoint_ind = random.randint(0, len(player_spawnpoints)-1)
        _, new_spawnpoint = player_spawnpoints.pop(spawnpoint_ind)
        player_pos.set_position(*new_spawnpoint.get_position())

    for _, robber_pos in world.query_component(Position, including=Robber):
        _, new_spawnpoint = random.choice(robber_spawnpoints)
        robber_pos.set_position(*new_spawnpoint.get_position())

def on_robber_death(resources: Resources, event: ComponentsRemovedEvent):
    state = resources[CurrentGameState]
    
    # We should make sure that the game is running, as 
    if state == GameState.InGame:

        if Robber in event.components:
            # A robber has died. The game should essentially end
            print("Policemen won!")

class CharactersHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(GameStartedEvent, on_game_started)
        app.add_event_listener(ComponentsRemovedEvent, on_robber_death)