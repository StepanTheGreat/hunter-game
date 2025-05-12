from core.assets import AssetManager
from core.graphics import Texture

from plugins.shared.entities.characters import *
from plugins.client.components import *

ROBBER_AMBIENT_LIGHT = (0.4, 0.8, 0.4)

CLIENT_ROBBER_PROJECTILE = ROBBER_PROJECTILE.copy()
CLIENT_ROBBER_PROJECTILE.user_components = (
    lambda: RenderPosition(),
)

CLIENT_POLICEMAN_PROJECTILE = POLICEMAN_PROJECTILE.copy()
CLIENT_POLICEMAN_PROJECTILE.user_components = (
    lambda: RenderPosition(),
)
    
def make_client_policeman(
    uid: int, 
    pos: tuple[float, float], 
    ismain: bool,
    assets: AssetManager
) -> tuple:

    texture = assets.load(Texture, "images/sprites.atl#character")

    components = make_policeman(uid, pos) + (
        RenderPosition(),
        Light(32, (1, 1, 1), 2500, 1.2),
        Sprite(0, texture, (32, 64)),
        RenderAngle(),
        PerspectiveAttachment(24, -1 if ismain else 0),
        Weapon(CLIENT_POLICEMAN_PROJECTILE, POLICEMAN_WEAPON_STATS),
    )
    if ismain:
        components += (MainPlayer(), )
    else:
        components += (InterpolatedPosition(), InterpolatedAngle())
    
    return components