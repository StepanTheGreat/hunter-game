"""
A collection of "commands" that 
"""

from plugin import Plugin

from plugins.shared.services.network import Server
from plugins.shared.actions import ActionDispatcher, Action

from plugins.server.services.clientlist import ClientList

from plugins.rpcs.client import *
from plugins.rpcs.pack import pack_angle

from typing import Callable, Optional, Any

class ServerAction(Action):
    """
    An action describes a procedure called from systems and addressed to remote receivers.
    Actions can be dispatched using action dispatchers, and by themselves they only represent
    individual network actions and arguments to which to perform them.
    
    They're the abstraction that allows high-level systems not to touch parsing structures, as actions
    should handle that themselves in their initialisation logic.
    """
    def __init__(self, rpc: Callable, args: tuple, to: tuple[int] = None):
        self.rpc: Callable = rpc
        self.args: tuple[Any, ...] = args
        self.to: Optional[tuple[int]] = to

class SyncPlayersAction(ServerAction):
    def __init__(self, entries: tuple[tuple[int, tuple[int, int], float, bool]]):
        data = bytes()
        for (uid, pos, angle, is_shooting) in entries:
            data += SYNC_PLAYERS_FORMAT.pack(
                uid, 
                int(pos[0]), 
                int(pos[1]),
                pack_angle(angle),
                is_shooting
            )

        super().__init__(
            sync_players_rpc, 
            (data, )
        )

class SpawnPlayerAction(ServerAction):
    "Spawn a player with a specific UID on a specific client (specified by its address)"
    def __init__(
        self, 
        client: int, 
        uid: int, 
        pos: tuple[int, int], 
        is_main: bool
    ):
        super().__init__(
            spawn_player_rpc, 
            (
                uid, 
                int(pos[0]),
                int(pos[1]),
                is_main
            ), 
            to=(client, )
        )

class SpawnDiamondsAction(ServerAction):
    "Spawn diamonds on the clients"
    def __init__(self, diamonds: tuple[tuple[int, tuple[int, int]]]):
        data = bytes()
        for (uid, (posx, posy)) in diamonds:
            data += SPAWN_DIAMONDS_FORMAT.pack(uid, int(posx), int(posy))

        super().__init__(
            spawn_diamonds_rpc, 
            (data, ),
            to = None
        )

class KillEntityAction(ServerAction):
    "An action that gets fired when a network entity gets killed (removed from the ECS world)"
    def __init__(self, uid: int):
        super().__init__(
            kill_entity_rpc,
            (uid, ),
            to=None
        )

class CrookifyPolicemanAction(ServerAction):
    "An action that gets fired at the start of the game, making a specific existing player a robber"
    def __init__(self, uid: int):
        super().__init__(
            crookify_policeman_rpc,
            (uid, ),
            to=None
        )

class SyncTimeAction(ServerAction):
    "An action that gets fired when a network entity gets killed (removed from the ECS world)"
    def __init__(self, time: float):
        super().__init__(
            sync_time_rpc,
            (time, ),
            to=None
        )

class SyncHealthAction(ServerAction):
    "An action that allows the hit player to know how much health they got left"
    
    def __init__(self, client: int, health: float):
        super().__init__(
            sync_player_health_rpc, 
            (health, ),
            to = (client, )
        )

@event
class TellReadyPlayersAction(ServerAction):
    "This action tells all players how many players are ready to start the game"

    def __init__(self, players_ready: int, players: int):
        super().__init__(
            tell_players_ready_rpc, 
            (players_ready, players),
            to = None
        )

@event
class GameNotificationAction(ServerAction):
    "This action that simply sends a simple game notification, like state transitions and so on"

    def __init__(self, notification: GameNotification):
        super().__init__(
            game_notification_rpc, 
            (notification.value, ),
            to = None
        )

class ServerActionDispatcher(ActionDispatcher):
    """
    A dispatcher is a command dispatcher for network actions. You push your actions directly here,
    and they will be dispatched on the server.
    """
    def __init__(self, resources: Resources):
        # The reason we're doing it here is because the Server is ALWAYS available on the server app
        self.server = resources[Server]
        self.clientlist = resources[ClientList]

    def _invoke_rpc(self, rpc: Callable, args: tuple[Any, ...], to: tuple[int] = None):
        "The internal method for invoking RPCs"

        if to is None:
            self.server.call_all(rpc, *args)
        else:
            for client_ent in to:
                if not self.clientlist.contains_client_ent(client_ent):
                    continue

                addr = self.clientlist.get_client_addr(client_ent)
                self.server.call(addr, rpc, *args)

    def dispatch_action(self, action: ServerAction):
        self._invoke_rpc(action.rpc, action.args, to=action.to)

class ServerActionPlugin(Plugin):
    def build(self, app):
        app.insert_resource(
            ServerActionDispatcher(app.get_resources())
        )