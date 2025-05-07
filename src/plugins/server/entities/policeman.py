from plugins.shared.components import *
from plugins.shared.entities.policeman import make_policeman
from plugins.shared.entities.robber import Robber

from .player import PlayerAddress

def make_server_policeman(
    addr: tuple[str, int], 
    uid: int, 
    pos: tuple[float, float]
) -> tuple:
    components = make_policeman(uid, pos) + (PlayerAddress(addr), Robber())
    
    return components