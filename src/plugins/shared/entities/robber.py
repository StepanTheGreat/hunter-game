from plugin import Plugin, Resources, Schedule

from core.ecs import component
from ..collisions import DynCollider

from ..components import *

from .projectile import ProjectileFactory
from .weapon import Weapon
from .player import Player, PlayerController

@component
class Robber:
    "A robber tag"

ROBBER_PROJECTILE = ProjectileFactory(
    False,
    speed=10,
    radius=20,
    damage=50,
    lifetime=0.1,
    spawn_offset=30,
)
    
def make_robber(uid: int, pos: tuple[float, float]) -> tuple:
    return (
        Position(*pos),
        Velocity(0, 0, 300),
        AngleVelocity(0, 4),
        Angle(0),
        DynCollider(18, 30),
        Weapon(ROBBER_PROJECTILE, 0.1, True),
        PlayerController(),
        Team.friend(),
        Hittable(),
        Health(2000, 0.25),
        Player()
    )

class RobberPlugin(Plugin):
    def build(self, app):
        pass