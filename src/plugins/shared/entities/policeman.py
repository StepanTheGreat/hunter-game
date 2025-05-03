from plugin import Plugin, Resources, Schedule

from core.ecs import component

from plugins.shared.collisions import DynCollider

from plugins.shared.components import *

from .projectile import ProjectileFactory
from .weapon import Weapon
from .player import Player, PlayerController

@component
class Policeman:
    "The policeman tag"

POLICEMAN_PROJECTILE = ProjectileFactory(
    False,
    speed=10,
    radius=20,
    damage=75,
    lifetime=0.1,
    spawn_offset=30,
)
    
def make_policeman(uid: int, pos: tuple[float, float]) -> tuple:
    components = (
        Position(*pos),
        Velocity(0, 0, 200),
        AngleVelocity(0, 4),
        Angle(0),
        DynCollider(12, 30),
        Weapon(POLICEMAN_PROJECTILE, 0.1, True),
        PlayerController(),
        Team.friend(),
        Hittable(),
        Health(500, 0.25),
        Player(),
    )
    
    return components

class PolicemanPlugin(Plugin):
    def build(self, app):
        pass
