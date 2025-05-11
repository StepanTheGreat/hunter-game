from plugin import Plugin, Resources

from core.ecs import WorldECS
from core.events import ComponentsAddedEvent

from plugins.rpcs.client import *
from plugins.client.components import *

from plugins.client.commands import ResetPlayerStatsHealthCommand, UpdatePlayerStatsHealthCommand

from plugins.shared.services.uidman import EntityUIDManager

from plugins.client.services.session import ServerTime
from plugins.client.components import MainPlayer

from plugins.shared.constants import SNAP_PLAYER_POSITION_DISTANCE

def on_sync_players_command(resources: Resources, command: SyncPlayersCommand):
    "Apply net syncronization on all requested players"

    world = resources[WorldECS]
    uidman = resources[EntityUIDManager]
    server_timer = resources[ServerTime]
    server_time = resources[ServerTime].get_current_time() + server_timer.get_server_offset()

    for (uid, new_pos, new_angle, is_shooting) in command.entries:
        ent = uidman.get_ent(uid)
        if ent is None:
            continue
        
        is_main = world.has_component(ent, MainPlayer)
        if is_main and world.has_component(ent, Position):
            pos = world.get_component(ent, Position)

            if pos.get_position().distance_to(new_pos) > SNAP_PLAYER_POSITION_DISTANCE:
                pos.set_position(*new_pos)
        elif world.has_components(ent, InterpolatedPosition, InterpolatedAngle, PlayerController):

            pos, angle, controller = world.get_components(ent, InterpolatedPosition, InterpolatedAngle, PlayerController)
            pos.push_position(server_time, *new_pos)
            angle.push_angle(server_time, new_angle)
            controller.is_shooting = is_shooting

def on_kill_entity_command(resources: Resources, command: KillEntityCommand):
    "When we receive an entity kill command from the server - we should kill said entity"

    world = resources[WorldECS]
    uidman = resources[EntityUIDManager]

    target_uid = command.uid
    target_ent = uidman.get_ent(target_uid)

    if target_ent is not None and world.contains_entity(target_ent):
        with world.command_buffer() as cmd:
            cmd.remove_entity(target_ent)

def on_new_main_player(resources: Resources, event: ComponentsAddedEvent):
    """
    This system runs every time a new main player is spawned, and its only purpose is to 
    reset the `HealthStats` global resource to 1.
    """
    
    if MainPlayer in event.components:
        resources[EventWriter].push_event(ResetPlayerStatsHealthCommand())

def on_sync_health_command(resources: Resources, command: SyncHealthCommand):
    world = resources[WorldECS]

    # When we receive this command, we would like to syncronize our health
    for _, health in world.query_component(Health, including=MainPlayer):
        health.set_percentage(command.health)

    # We're also going to update the `PlayerStats`, though I think this should probably
    # be done from a separate event listener instead
    resources[EventWriter].push_event(UpdatePlayerStatsHealthCommand(command.health))

def on_players_ready_command(resources: Resources, command: PlayersReadyCommand):
    print(f"Players ready update: {command.players_ready}/{command.players}")

class SessionHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(SyncPlayersCommand, on_sync_players_command)
        app.add_event_listener(KillEntityCommand, on_kill_entity_command)

        app.add_event_listener(ComponentsAddedEvent, on_new_main_player)
        app.add_event_listener(SyncHealthCommand, on_sync_health_command)
        app.add_event_listener(PlayersReadyCommand, on_players_ready_command)