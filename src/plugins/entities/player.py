import pygame as pg
import numpy as np

from plugin import Plugin, Resources, Schedule

from core.graphics import Camera3D
from core.pg import Clock
from core.ecs import WorldECS, component
from core.input import InputManager
from plugins.collisions import DynCollider

from plugins.graphics.lights import Light

from plugins.components import *

from .projectile import ProjectileFactory
from .weapon import Weapon

class PlayerStats:
    "Stores global player related information. Useful for GUI and visualisations, since its a shared resource"
    def __init__(self, health: Health):
        self.health: float = health.get_percentage()
        "Stores the player's health in percentages"

    def update_health(self, health: Health):
        self.health = health.get_percentage()

    def get_health(self) -> float:
        return self.health

class InputAction:
    Forward = "move_forward"
    Backwards = "move_backwards"
    Left = "move_left"
    Right = "move_right"

    TurnLeft = "turn_left"
    TurnRight = "turn_right"

    Shoot = "shoot"

@component
class Player:
    "A tag component that allows filtering out players"

@component
class PlayerController:
    def __init__(self):
        self.forward_dir = 0
        self.horizontal_dir = 0

PLAYER_PROJECTILE = ProjectileFactory(
    False,
    speed=0,
    radius=20,
    damage=150,
    lifetime=0.1,
    spawn_offset=30,
)
    
def make_player(pos: tuple[float, float]) -> tuple:
    return (
        Position(*pos),
        RenderPosition(*pos, 44),
        Velocity(0, 0, 150),
        Light((1, 1, 1), 300),
        AngleVelocity(0, 4),
        Angle(0),
        RenderAngle(0),
        DynCollider(12, 30),
        Weapon(PLAYER_PROJECTILE, 0.5, 0, True),
        PlayerController(),
        Team.friend(),
        Hittable(),
        Health(200),
        Player()
    )

def control_player(resources: Resources):
    input = resources[InputManager]
    world = resources[WorldECS]

    for ent, (controller, angle_vel, weapon) in world.query_components(PlayerController, AngleVelocity, Weapon):
        angle_vel.set_velocity(input[InputAction.TurnRight]-input[InputAction.TurnLeft])
        controller.forward_dir = input[InputAction.Forward]-input[InputAction.Backwards]
        controller.horizontal_dir = input[InputAction.Right]-input[InputAction.Left]

        if input[InputAction.Shoot]:
            weapon.start_shooting()
        else:
            weapon.stop_shooting()

def orient_player(resources: Resources):
    world = resources[WorldECS]

    for ent, (controller, vel, angle) in world.query_components(PlayerController, Velocity, Angle):
        forward = controller.forward_dir
        horizontal = controller.horizontal_dir
        
        current_angle = angle.get_angle()

        forward_vel = pg.Vector2(0, 0)
        horizontal_vel = pg.Vector2(0, 0)
        if forward != 0:
            forward_vel = pg.Vector2(np.cos(current_angle), np.sin(current_angle)) * forward
        if horizontal != 0:
            horizontal_angle = current_angle+np.pi/2*horizontal
            horizontal_vel = pg.Vector2(np.cos(horizontal_angle), np.sin(horizontal_angle))

        new_vel = horizontal_vel+forward_vel
        if new_vel.length_squared() != 0.0:
            new_vel.normalize_ip()

        vel.set_velocity(new_vel.x, new_vel.y)

def move_camera(resources: Resources):
    camera = resources[Camera3D]

    for _, (position, angle) in resources[WorldECS].query_components(RenderPosition, RenderAngle, including=Player):
        camera.set_pos(position.get_position())
        camera.set_angle(angle.get_angle())
        break

def make_test_lights(resources: Resources):
    world = resources[WorldECS]

    for (x, y) in ((3*48, 5*48),):
        world.create_entity(
            Position(x, y),
            RenderPosition(x, y, 24),
            Light((0.3, 0.5, 1), 1000)
        )

class PlayerPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Startup, make_test_lights)
        app.add_systems(Schedule.Update, control_player)
        app.add_systems(Schedule.FixedUpdate, orient_player, priority=-1)
        app.add_systems(Schedule.PreDraw, move_camera)
