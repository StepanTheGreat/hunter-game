from core.assets import AssetManager
from core.graphics import Texture

from core.assets import AssetManager

from plugins.shared.entities.diamond import *
from plugins.client.components import *

def make_client_diamond(uid: int, pos: tuple[int, int], assets: AssetManager):
    "A shared diamond entity with visual components"

    texture = assets.load(Texture, "images/sprites.atl#diamond")

    components = make_diamond(uid, pos)
    components += (
        RenderPosition(),
        Light(8, (1, 1, 1), 250, 1.2),
        Sprite(0, texture, (16, 16)),
    )

    return components