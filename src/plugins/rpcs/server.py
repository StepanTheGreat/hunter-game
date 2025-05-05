from plugin import Resources, EventWriter, event

from plugins.shared.network import rpc, rpc_raw, get_rpc_caller_addr
from .pack import unpack_velocity, unpack_angle

from modules.utils import clamp

@event
class ControlPlayerCommand:
    """
    A player under a specific address (client) has requested to move to a certain point, with
    a specific velocity
    """
    def __init__(
        self, 
        addr: tuple[str, int], 
        pos: tuple[int, int], 
        vel: tuple[float, float],
        angle: float,
        angle_vel: float,
        is_shooting: bool
    ):
        self.addr = addr
        self.pos = pos
        self.vel = vel
        self.angle = angle
        self.angle_vel = angle_vel
        self.is_shooting = is_shooting

@rpc("2hB?Bb?")
def control_player_rpc(
    resources: Resources, 
    pos_x: int, pos_y: int, 
    vel_angle: int, vel_length: bool,
    angle: int, angle_vel: float,
    is_shooting: bool
):
    ewriter = resources[EventWriter]

    ewriter.push_event(ControlPlayerCommand(
        get_rpc_caller_addr(),
        (pos_x, pos_y),
        unpack_velocity(vel_angle, vel_length),
        unpack_angle(angle),
        clamp(angle_vel, -1, 1),
        is_shooting
    ))

SERVER_RPCS = (
    control_player_rpc,
)
"The RPCs used by the server"