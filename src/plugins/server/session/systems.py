from plugin import Plugin, Schedule, Resources

from plugins.shared.network import Server
from plugins.rpcs.listener import notify_available_server_rpc, LISTENER_PORT

from ..actions import SyncTimeAction, ServerActionDispatcher

from modules.time import Clock, Timer

from .session import GameSession, GameState, MAX_PLAYERS

class SyncClientTimeTimer:
    "This timer simply tracks when the server should notify the clients of its time"
    NOTIFY_EVERY = 5

    def __init__(self):
        self.notify_timer = Timer(SyncClientTimeTimer.NOTIFY_EVERY, True)

    def tick(self, dt: float):
        self.notify_timer.tick(dt)

    def should_notify(self) -> bool:
        return self.notify_timer.has_finished()
    
    def reset(self):
        self.notify_timer.reset()

def tick_sync_client_timer(resources: Resources):
    dispatcher = resources[ServerActionDispatcher]
    sync_timer = resources[SyncClientTimeTimer]
    clock = resources[Clock]

    sync_timer.tick(clock.get_delta())

    if sync_timer.should_notify():
        dispatcher.dispatch_action(SyncTimeAction(
            clock.get_execution_time(),
            clock.get_execution_time()
        ))

        sync_timer.reset()

def broadcast_server(resources: Resources):
    session = resources[GameSession]
    server = resources[Server]
    dt = resources[Clock].get_delta()

    if session.game_state == GameState.WaitingForPlayers:
        broadcast_timer = session.broadcast_timer

        broadcast_timer.tick(dt)
        if broadcast_timer.has_finished():
            server.broadcast(
                LISTENER_PORT, 
                notify_available_server_rpc, 
                MAX_PLAYERS,
                session.taken_player_slots()
            )
            broadcast_timer.reset()

class SessionSystemsPlugin(Plugin):
    def build(self, app):
        # In this plugin we're going to initialize the game session resource and the server
        app.add_systems(Schedule.Update, broadcast_server)

        app.insert_resource(SyncClientTimeTimer())
        app.add_systems(Schedule.Update, tick_sync_client_timer)
