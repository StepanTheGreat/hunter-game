"""
A collection of "commands" that 
"""

from plugin import Plugin

from plugins.shared.network import Client
from plugins.shared.actions import ActionDispatcher, Action

from plugins.rpcs.server import *
<<<<<<< HEAD
from plugins.rpcs.pack import pack_velocity
=======
from plugins.rpcs.pack import pack_velocity, pack_angle
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75

from typing import Callable, Optional, Any

class ClientAction(Action):
    """
    An action describes a procedure called from systems and addressed to remote receivers.
    Actions can be dispatched using action dispatchers, and by themselves they only represent
    individual network actions and arguments to which to perform them.
    
    They're the abstraction that allows high-level systems not to touch parsing structures, as actions
    should handle that themselves in their initialisation logic.
    """
<<<<<<< HEAD
    def __init__(self, rpc: Callable, *args):
=======
    def __init__(self, rpc: Callable, args):
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
        self.rpc: Callable = rpc
        self.args: tuple[Any, ...] = args

class ControlAction(ClientAction):
    "Tell the player the position and velocity of your player"

<<<<<<< HEAD
    def __init__(self, pos: tuple[int, int], vel: tuple[float, float]):
        super().__init__(
            control_player_rpc, 
            int(pos[0]), int(pos[1]), *pack_velocity(*vel)
=======
    def __init__(
        self, 
        pos: tuple[int, int], 
        vel: tuple[float, float],
        angle: float,
        angle_vel: float,
        is_shooting: bool 
    ):
        super().__init__(
            control_player_rpc, 
            (
                int(pos[0]), int(pos[1]), *pack_velocity(*vel),
                pack_angle(angle), 
                int(angle_vel), 
                is_shooting
            )
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
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