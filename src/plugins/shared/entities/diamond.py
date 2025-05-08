from plugins.shared.components import *

def make_diamond(uid: int, pos: tuple[int, int]) -> tuple:
    components = (
        Position(*pos),
        NetEntity(uid),
        PickingUp(),
        Diamond()
    )
    
    return components