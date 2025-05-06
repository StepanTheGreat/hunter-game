"""
A collection of "commands" that 
"""

from plugin import Plugin

from plugins.shared.network import Client
from plugins.shared.actions import ActionDispatcher, Action

from plugins.rpcs.server import *
from plugins.rpcs.pack import pack_velocity

from typing import Callable, Optional, Any

class ClientAction(Action):
    """
    An action describes a procedure called from systems and addressed to remote receivers.
    Actions can be dispatched using action dispatchers, and by themselves they only represent
    individual network actions and arguments to which to perform them.
    
    They're the abstraction that allows high-level systems not to touch parsing structures, as actions
    should handle that themselves in their initialisation logic.
    """
    def __init__(self, rpc: Callable, *args):
        self.rpc: Callable = rpc
        self.args: tuple[Any, ...] = args

class ControlAction(ClientAction):
    "Tell the player the position and velocity of your player"

    def __init__(self, pos: tuple[int, int], vel: tuple[float, float]):
        super().__init__(
            control_player_rpc, 
            int(pos[0]), int(pos[1]), *pack_velocity(*vel)
        )

class ClientActionDispatcher(ActionDispatcher):
    """
    A dispatcher is a command dispatcher for network actions. You push your actions directly here,
    and they will be dispatched on the server.
    """
    def __init__(self, resources: Resources):
        self.resources = resources

    def _invoke_rpc(self, rpc: Callable, args: tuple[Any, ...]):
        "The internal method for invoking RPCs"
        
        # Because we would like to run client logic even without a server - we will simply
        # not do anything if the client isn't present currently. Our systems shouldn't care about
        # the internal state of networking - it simply throws actions.
        client = self.resources.get(Client)
        if client is None:
            return
        
        client.call(rpc, *args)

    def dispatch_action(self, action: ClientAction):
        self._invoke_rpc(action.rpc, action.args)

class ClientActionPlugin(Plugin):
    def build(self, app):
        app.insert_resource(
            ClientActionDispatcher(app.get_resources())
        )