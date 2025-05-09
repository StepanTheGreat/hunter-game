from plugin import Plugin

from plugins.shared.network import Client

from plugins.rpcs.server import *
from plugins.rpcs.pack import pack_velocity

from typing import Callable, Any

class Action:
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

class ActionDispatcher:
    """
    A dispatcher is a command dispatcher for network actions. You push your actions directly here,
    and they will be dispatched on the server.
    """
    def __init__(self, resources: Resources):
        self.resources = resources

    def dispatch_action(self, action: Action):
        "The public action dispatching interface"

