from plugin import Plugin, Resources

from core.time import SystemScheduler, schedule_systems_seconds
from core.ecs import WorldECS

from plugins.server.components import Client

from plugins.server.commands import StopServerBroadcastingCommand
from plugins.shared.services.network import BroadcastWriter, Server

from plugins.rpcs.listener import notify_available_server_rpc, LISTENER_PORT

from plugins.server.constants import BROADCAST_FREQUENCY, MAX_PLAYERS

def broadcast_server(resources: Resources):
    server = resources[Server]
    world = resources[WorldECS]
    broadcaster = resources[BroadcastWriter]

    server_ip, server_port = server.get_addr()
    players_len = len(world.query_component(Client))

    broadcaster.broadcast_call(
        LISTENER_PORT,
        notify_available_server_rpc,

        *(int(ip_component) for ip_component in server_ip.split(".")),
        server_port,
        MAX_PLAYERS,
        players_len
    )

def on_stop_broadcasting_command(resources: Resources, _):
    resources[SystemScheduler].remove_scheduled(broadcast_server)

class ServerBroadcasterPlugin(Plugin):
    def build(self, app):
        # In this plugin we're going to initialize the game session resource and the server
        schedule_systems_seconds(
            app,
            (broadcast_server, BROADCAST_FREQUENCY, True),
        )

        app.add_event_listener(StopServerBroadcastingCommand, on_stop_broadcasting_command)