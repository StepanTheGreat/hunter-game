from plugin import Plugin, Resources, Schedule

from core.assets import AssetManager
from core.graphics import Texture

from plugins.shared.entities.weapon import Weapon

from plugins.client.graphics.lights import Light
from plugins.client.graphics.sprite import Sprite
from plugins.client.perspective import PerspectiveAttachment

from core.assets import AssetManager

from plugins.shared.entities.diamond import *
from plugins.client.components import *

def make_client_diamond(uid: int, pos: tuple[int, int], assets: AssetManager):

    texture = assets.load(Texture, "images/sprites.atl#diamond")

    components = make_diamond(uid, pos)
    components += (
        RenderPosition(0),
        Light((1, 1, 1), 2000, 1.2),
        Sprite(texture, (16, 16)),
    )