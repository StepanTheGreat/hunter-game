import pygame as pg
import numpy as np

from plugin import Plugin, Resources, Schedule

from core.ecs import WorldECS, component
from core.input import InputManager
from plugins.collisions import DynCollider

from plugins.graphics.lights import Light
from plugins.perspective import PerspectiveAttachment

from plugins.components import *

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
    
def make_robber(pos: tuple[float, float]) -> tuple:
    return (
        Position(*pos),
        RenderPosition(*pos, 24),
        Velocity(0, 0, 300),
        AngleVelocity(0, 4),
        Angle(0),
        RenderAngle(0),
        DynCollider(18, 30),
        Weapon(ROBBER_PROJECTILE, 0.1, True),
        PlayerController(),
        Team.friend(),
        Hittable(),
        Health(2000, 0.25),
        PerspectiveAttachment(24, 0),
        Player()
    )

class RobberPlugin(Plugin):
    def build(self, app):
        pass