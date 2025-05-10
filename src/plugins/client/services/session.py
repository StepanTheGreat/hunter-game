"Session-related code"

from core.time import Clock

from plugins.rpcs.client import SyncTimeCommand

from plugin import Plugin, Resources, Schedule

from collections import deque

from typing import Optional

class ServerTime:
    SERVER_OFFSETS = 5
    "We will store 5 different offsets and average them"

    def __init__(self):
        self.current_time = 0
        self.ticking = False

        self.server_offsets: deque[float] = deque()

    def start(self):
        "Start this clock"
        self.ticking = True

    def stop_and_reset(self):
        "Stop and reset this clock"
        self.ticking = False
        self.current_time = 0

        self.server_offsets.clear()

    def tick(self, dt: float):
        if self.ticking:
            self.current_time += dt

    def sync_time(self, new_time: float):
        """
        Syncronize this time with the server's. It takes 2 arguments: the timestamp (to know when
        the packet command was issued) and the current server time.
        """

        # Add the difference as the last entry
        self.server_offsets.append(new_time-self.current_time)

        # If we have more than the maximum amount of offsets - remove the oldest one
        if len(self.server_offsets) > ServerTime.SERVER_OFFSETS:
            self.server_offsets.popleft()

    def _get_average_offset(self) -> float:
        "Return the average server offset. Will raise an exception if the queue is empty"

        return sum(self.server_offsets) / len(self.server_offsets)

    def get_server_offset(self) -> float:
        "Get the current server offset. If not yet received - returns 0"

        return self._get_average_offset() if len(self.server_offsets) > 0 else 0

    def get_current_time(self) -> float:
        return self.current_time

def tick_server_time(resources: Resources):
    "Tick the clock every frame. If it's running of course, in any other case it doesn't do anything."

    dt = resources[Clock].get_delta()
    resources[ServerTime].tick(dt)

def on_sync_time_command(resources: Resources, command: SyncTimeCommand):
    resources[ServerTime].sync_time(command.time)

class SessionPlugin(Plugin):
    def build(self, app):
        app.insert_resource(ServerTime())
        app.add_systems(Schedule.First, tick_server_time)
        app.add_event_listener(SyncTimeCommand, on_sync_time_command)