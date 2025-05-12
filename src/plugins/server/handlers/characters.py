from plugin import Plugin, Resources, EventWriter

from core.ecs import WorldECS
from core.events import ComponentsRemovedEvent

from plugins.server.events import GameStartedEvent, GameFinishedEvent, LightsOnEvent
from plugins.server.actions import *
from plugins.server.components import *

# TODO: Remove this things
from plugins.shared.entities.characters import crookify_policeman
from plugins.server.services.state import CurrentGameState, GameState, LightsOn

import random

def teleport_and_buff_on_game_started(resources: Resources, _):
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

    # Now we're going to buff policemen

    policemen = world.query_component(Policeman)    
    damage_mult = 1/max(len(policemen), 1) 
    # We're going to reduce the damage based on the amount of policemen. More = less

    # Add to each a damage multiplier component with said damage rate
    for ent, _ in policemen:
        world.add_components(ent, DamageMultiplier(damage_mult))

def on_robber_death(resources: Resources, event: ComponentsRemovedEvent):
    "This handler changes the current state of the game and pushed the victory notifications whenever the robber has died"

    state = resources[CurrentGameState]
    ewriter = resources[EventWriter]
    dispatcher = resources[ServerActionDispatcher]
    
    # We should make sure that the game is running and it's indeed the robber that was killed
    if state != GameState.InGame:
        return
    if Robber not in event.components:
        return
    
    # A robber has died. The game should essentially end
    dispatcher.dispatch_action(GameNotificationAction(GameNotification.PolicemenWon))
    ewriter.push_event(GameFinishedEvent())

def on_policeman_death(resources: Resources, event: ComponentsRemovedEvent):
    """
    This handler tracks all policeman deaths, and if the game has started and the lights are off - it's
    going to turn them on and push a notification to all clients
    """

    world = resources[WorldECS]
    state = resources[CurrentGameState]
    ewriter = resources[EventWriter]
    dispatcher = resources[ServerActionDispatcher]

    if state != GameState.InGame:
        # The game should start
        return
    elif Policeman not in event.components:
        # Only policemen should count
        return
    elif world.contains_entity(event.entity):
        # If a policeman component was removed but the entity is still alive... It means it was
        # a crookification, thus doesn't count either
        return
    elif LightsOn in resources:
        # If the lights are already on - there's no reason
        return

    dispatcher.dispatch_action(GameNotificationAction(GameNotification.LightsOn))
    ewriter.push_event(LightsOnEvent())
    

class CharactersHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(GameStartedEvent, teleport_and_buff_on_game_started)

        app.add_event_listener(ComponentsRemovedEvent, on_robber_death)
        app.add_event_listener(ComponentsRemovedEvent, on_policeman_death)