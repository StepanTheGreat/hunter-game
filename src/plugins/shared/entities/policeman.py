from plugin import Plugin, Resources, Schedule

from core.ecs import component

from plugins.shared.collisions import DynCollider

from plugins.shared.components import *

from .projectile import ProjectileFactory
from .weapon import Weapon, WeaponStats
from .player import Player, PlayerController

@component
class Policeman:
    "The policeman tag"

POLICEMAN_PROJECTILE = ProjectileFactory(
    True,
    speed=500,
    radius=5,
    damage=15,
    lifetime=1,
    spawn_offset=24,
)

POLICEMAN_WEAPON_STATS = WeaponStats(0.1, True)
    
def make_policeman(uid: int, pos: tuple[float, float]) -> tuple:
    components = (
        Position(*pos),
        Velocity(0, 0, 200),
        AngleVelocity(0, 4),
        Angle(0),
        DynCollider(12, 30),
        Weapon(POLICEMAN_PROJECTILE, POLICEMAN_WEAPON_STATS),
        PlayerController(),
        Team.friend(),
        Hittable(),
        Health(500, 0.25),
        NetEntity(uid),
        NetSyncronized(),
        Player(),
    )
    
    return components

class PolicemanPlugin(Plugin):
    def build(self, app):
        pass
