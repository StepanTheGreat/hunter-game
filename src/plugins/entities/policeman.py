from plugin import Plugin, Resources, Schedule

from core.ecs import WorldECS, component
from plugins.collisions import DynCollider

from plugins.graphics.lights import Light
from plugins.perspective import PerspectiveAttachment

from plugins.components import *

from .projectile import ProjectileFactory
from .weapon import Weapon
from .player import Player, PlayerController

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
    
def make_policeman(pos: tuple[float, float]) -> tuple:
    return (
        Position(*pos),
        RenderPosition(*pos, 24),
        Velocity(0, 0, 200),
        Light((1, 1, 1), 20000, 1.2),
        AngleVelocity(0, 4),
        Angle(0),
        RenderAngle(0),
        DynCollider(12, 30),
        Weapon(POLICEMAN_PROJECTILE, 0.1, True),
        PlayerController(),
        Team.friend(),
        Hittable(),
        Health(500, 0.25),
        PerspectiveAttachment(24, 0),
        Player()
    )

class PolicemanPlugin(Plugin):
    def build(self, app):
        pass
