from plugin import Plugin, Resources

from core.ecs import WorldECS

from ..actions import SyncTimeAction, ServerActionDispatcher

from core.time import Clock, schedule_systems_seconds

from plugins.server.components import *
from plugins.server.actions import *

def tick_sync_client_timer_system(resources: Resources):
    "This system runs in a while and essentially syncronizes client's clock with the server's"

    dispatcher = resources[ServerActionDispatcher]
    clock = resources[Clock]
    
    # Once in a while, we're going to syncronize client's clock with ours
    dispatcher.dispatch_action(SyncTimeAction(clock.get_execution_time()))

def sync_players_system(resources: Resources):
    """
    Syncronize all movable entities by collecting their UIDs, positions, angles and shooting statuses,
    sending them over network
    """

    world = resources[WorldECS]
    action_dispatcher = resources[ServerActionDispatcher]

    moved_entries = []

    for _, (ent, pos, angle, controller) in world.query_components(NetEntity, Position, Angle, PlayerController, including=NetSyncronized):
        uid = ent.get_uid()

        pos = pos.get_position()
        angle = angle.get_angle()
        is_shooting = controller.is_shooting

        moved_entries.append((uid, (pos.x, pos.y), angle, is_shooting))

    action_dispatcher.dispatch_action(SyncPlayersAction(
        tuple(moved_entries)
    )) 

class SyncSystemsPlugin(Plugin):
    def build(self, app):
        # In this plugin we're going to initialize the game session resource and the server
        schedule_systems_seconds(
            app,
            (tick_sync_client_timer_system, 5, True)
        )

        # We would like to syncronize our movables 20 times a second
        schedule_systems_seconds(app, (sync_players_system, 1/20, True))