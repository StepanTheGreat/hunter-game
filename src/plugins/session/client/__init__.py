from plugin import Plugin, Schedule, Resources

from plugins.entities.player import PlayerControlRequestEvent
from plugins.session.server.rpcs import control_player

from plugins.network import only_client, Client
from ..pack import pack_velocity

from .rpcs import *

@only_client
def on_player_control_event(resources: Resources, event: PlayerControlRequestEvent):
    client = resources[Client]

    pos = (int(event.pos[0]), int(event.pos[1]))
    vel = (event.vel[0], event.vel[1])

    client.call(control_player, *pos, *pack_velocity(*vel))

class ClientPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(PlayerControlRequestEvent, on_player_control_event)