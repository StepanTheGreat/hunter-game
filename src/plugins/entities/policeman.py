from plugin import Plugin, Resources, Schedule

from core.ecs import WorldECS, component
from core.assets import AssetManager
from core.graphics import Texture

from plugins.collisions import DynCollider
from plugins.graphics.lights import Light
from plugins.graphics.sprite import Sprite
from plugins.perspective import PerspectiveAttachment

from plugins.components import *
from plugins.session.components import NetEntity, NetSyncronized

from .projectile import ProjectileFactory
from .weapon import Weapon
from .player import Player, PlayerController, MainPlayer

@component
class Policeman:
    "The policeman tag"

POLICEMAN_PROJECTILE = ProjectileFactory(
    False,
    speed=0,
    radius=20,
    damage=75,
    lifetime=0.1,
    spawn_offset=30,
)
    
def make_policeman(
    uid: int, 
    pos: tuple[float, float], 
    ismain: bool,
    assets: AssetManager
) -> tuple:

    texture = assets.load(Texture, "images/sprites.atl#character")

    components = (
        Position(*pos),
        RenderPosition(*pos, 24),
        Velocity(0, 0, 200),
        Light((1, 1, 1), 20000, 1.2),
        Sprite(texture, (32, 64)),
        AngleVelocity(0, 4),
        Angle(0),
        RenderAngle(0),
        DynCollider(12, 30),
        Weapon(POLICEMAN_PROJECTILE, 0.1, True),
        PlayerController(),
        Team.friend(),
        Hittable(),
        Health(500, 0.25),
        PerspectiveAttachment(24, 0-ismain),
        NetSyncronized(),
        NetEntity(uid),
        Player(),
    )
    if ismain:
        components += (MainPlayer(), )
    
    return components

class PolicemanPlugin(Plugin):
    def build(self, app):
        pass
