from plugin import Resources, EventWriter, event

from plugins.shared.network import rpc, rpc_raw

@event
class ControlPlayerCommand:
    """
    A player under a specific address (client) has requested to move to a certain point, with
    a specific velocity
    """
    def __init__(self, addr: tuple[str, int], pos: tuple[int, int], vel: tuple[float, float]):
        self.addr = addr
        self.pos = pos
        self.vel = vel

@rpc("2hB?")
def control_player(
    resources: Resources, 
    pos_x: int, pos_y: int, 
    vel_angle: int, vel_length: bool):
    ewriter = resources[EventWriter]

    ewriter.push_event(ControlPlayerCommand(
        get_rpc_caller_addr(),
        (pos_x, pos_y),
        unpack_velocity(vel_angle, vel_length)
    ))

SERVER_RPCS = (
    control_player,
)
"The RPCs used by the server"