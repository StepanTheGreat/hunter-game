from plugins.shared.components import *
from plugins.shared.entities.policeman import make_policeman

from .player import PlayerAddress

def make_server_policeman(
    addr: tuple[str, int], 
    uid: int, 
    pos: tuple[float, float]
) -> tuple:
    components = make_policeman(uid, pos) + (PlayerAddress(addr), )
    
    return components