from plugin import Plugin, Schedule, Resources

from plugins.shared.network import Server, BroadcastWriter
from plugins.rpcs.listener import notify_available_server_rpc, LISTENER_PORT

from ..actions import SyncTimeAction, ServerActionDispatcher

from core.time import Clock, SystemScheduler, schedule_systems_seconds
from modules.utils import Timer

from .session import GameSession, GameState, MAX_PLAYERS, GameStartedEvent

BROADCAST_FREQUENCY = 5

def tick_sync_client_timer(resources: Resources):
    dispatcher = resources[ServerActionDispatcher]
    clock = resources[Clock]
    
    # Once in a while, we're going to syncronize client's clock with ours
    dispatcher.dispatch_action(SyncTimeAction(clock.get_execution_time()))

def broadcast_server(resources: Resources):
    session = resources[GameSession]
    broadcaster = resources[BroadcastWriter]

    if session.game_state != GameState.WaitingForPlayers:
        # If we're no longer waiting for players - we're going to remove this system
        resources[SystemScheduler].remove_scheduled(broadcast_server)
        return

    server_ip, server_port = resources[Server].get_addr()
    broadcaster.broadcast_call(
        LISTENER_PORT, 
        notify_available_server_rpc, 
        *(int(ip_component) for ip_component in server_ip.split(".")),
        server_port,
        MAX_PLAYERS,
        session.taken_player_slots()
    )

def on_game_started(resources: Resources, _):

    # We will stop broadcasting when the game starts
    resources[SystemScheduler].remove_scheduled(broadcast_server)

class SessionSystemsPlugin(Plugin):
    def build(self, app):
        # In this plugin we're going to initialize the game session resource and the server
        schedule_systems_seconds(
            app,
            (broadcast_server, BROADCAST_FREQUENCY, True),
            (tick_sync_client_timer, 5, True)
        )

        app.add_event_listener(GameStartedEvent, on_game_started)