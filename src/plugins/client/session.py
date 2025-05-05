"Session-related code"

from modules.time import Clock

from plugins.rpcs.client import SyncTimeCommand

from plugin import Plugin, Resources, Schedule

class ServerTime:
    def __init__(self):
        self.current_time = 0
        self.ticking = False

    def start(self):
        "Start this clock"
        self.ticking = True

    def stop_and_reset(self):
        "Stop and reset this clock"
        self.ticking = False
        self.current_time = 0

    def tick(self, dt: float):
        if self.ticking:
            self.current_time += dt

    def sync_time(self, timestamp: float, new_time: float):
        """
        Syncronize this time with the server's. It takes 2 arguments: the timestamp (to know when
        the packet command was issued) and the current server time.
        """

        # We're compensating for packet's latency here
        diff = self.current_time-timestamp
        self.current_time = new_time + diff

    def get_current_time(self) -> float:
        return self.current_time

def tick_server_time(resources: Resources):
    "Tick the clock every frame. If it's running of course, in any other case it doesn't do anything."

    dt = resources[Clock].get_delta()
    resources[ServerTime].tick(dt)

def on_sync_time_command(resources: Resources, command: SyncTimeCommand):
    resources[ServerTime].sync_time(command.timestamp, command.time)

class SessionPlugin(Plugin):
    def build(self, app):
        app.insert_resource(ServerTime())
        app.add_systems(Schedule.First, tick_server_time)
        app.add_event_listener(SyncTimeCommand, on_sync_time_command)