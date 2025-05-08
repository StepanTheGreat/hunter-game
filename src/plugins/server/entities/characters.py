from plugins.server.components import *
from plugins.shared.entities.characters import make_policeman

def make_server_policeman(
    owned_by: int, 
    uid: int, 
    pos: tuple[float, float]
) -> tuple:
    components = make_policeman(uid, pos) + (OwnedByClient(owned_by), )
    
    return components
