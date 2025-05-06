"""
A collection of "commands" that 
"""

from plugin import Plugin

from plugins.shared.network import Server
from plugins.shared.actions import ActionDispatcher, Action

from plugins.rpcs.client import *
from plugins.rpcs.pack import pack_velocity

from typing import Callable, Optional, Any

class ServerAction(Action):
    """
    An action describes a procedure called from systems and addressed to remote receivers.
    Actions can be dispatched using action dispatchers, and by themselves they only represent
    individual network actions and arguments to which to perform them.
    
    They're the abstraction that allows high-level systems not to touch parsing structures, as actions
    should handle that themselves in their initialisation logic.
    """
    def __init__(self, rpc: Callable, args: tuple, to: tuple[tuple[str, int]] = None):
        self.rpc: Callable = rpc
        self.args: tuple[Any, ...] = args
        self.to: Optional[tuple[tuple[str, int]]] = to

class MoveNetsyncedEntitiesAction(ServerAction):
    def __init__(self, entries: tuple[tuple[int, tuple[int, int], tuple[float, float]]]):
        data = bytes()
        for (uid, pos) in entries:
            data += MOVE_NETSYNCED_ENTITIES_FORMAT.pack(uid, int(pos[0]), int(pos[1]))

        super().__init__(
            move_netsynced_entities_rpc, 
            (data, )
        )

class SpawnPlayerAction(ServerAction):
    "Spawn a player with a specific UID on a specific client (specified by its address)"
    def __init__(
        self, 
        client: tuple[str, int], 
        uid: int, 
        pos: tuple[int, int], 
        is_main: bool
    ):
        super().__init__(
            spawn_player_rpc, 
            (
                uid, 
                *pos, 
                is_main
            ), 
            to=(client, )
        )

class KillEntityAction(ServerAction):
    "An action that gets fired when a network entity gets killed (removed from the ECS world)"
    def __init__(self, uid: int):
        super().__init__(
            kill_entity_rpc,
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

class ServerActionDispatcher(ActionDispatcher):
    """
    A dispatcher is a command dispatcher for network actions. You push your actions directly here,
    and they will be dispatched on the server.
    """
    def __init__(self, resources: Resources):
        # The reason we're doing it here is because the Server is ALWAYS available on the server app
        self.server = resources[Server]

    def _invoke_rpc(self, rpc: Callable, args: tuple[Any, ...], to: tuple[tuple[str, int]] = None):
        "The internal method for invoking RPCs"

        if to is None:
            self.server.call_all(rpc, *args)
        else:
            for addr in to:
                self.server.call(addr, rpc, *args)

    def dispatch_action(self, action: ServerAction):
        self._invoke_rpc(action.rpc, action.args, to=action.to)

class ServerActionPlugin(Plugin):
    def build(self, app):
        app.insert_resource(
            ServerActionDispatcher(app.get_resources())
        )