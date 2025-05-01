from plugin import Resources

from core.ecs import WorldECS

from plugins.network import rpc, rpc_raw, only_client
from plugins.components import Position, Velocity

from typing import Iterable, Sequence
from struct import Struct

from ..pack import unpack_velocity
from ..components import NetEntity