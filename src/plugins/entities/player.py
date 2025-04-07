import pygame as pg
import numpy as np

from plugin import Plugin, Resources, Schedule

from core.graphics import Camera3D
from core.entity import EntityWorld, Entity
from core.input import InputManager
from core.collisions import CollisionManager, DynCollider

from modules.inteprolation import InterpolatedAngle

class InputAction:
    Forward = "move_forward"
    Backwards = "move_backwards"
    Left = "move_left"
    Right = "move_right"

    TurnLeft = "turn_left"
    TurnRight = "turn_right"

class Player(Entity):
    HITBOX_SIZE = 14
    SPEED = 250
    ROTATION_SPEED = 3

    def __init__(self, uid: int, pos: tuple[float, float], collisions: CollisionManager):
        super().__init__(uid)

        self.collider = DynCollider(Player.HITBOX_SIZE, pos, 10)

        self.angle_vel = 0
        self.forward_vel = 0
        self.horizontal_vel = 0

        self.rect = pg.Rect(0, 0, Player.HITBOX_SIZE, Player.HITBOX_SIZE)
        self.vel = pg.Vector2(0, 0)
        self.angle = 0

        self.angles = InterpolatedAngle(self.angle)
        self.interpolated_angle = self.angles.get_value()

        collisions.add_collider(self.collider)
        
    def update_fixed(self, dt: float):
        forward = self.forward_vel
        horizontal = self.horizontal_vel

        forward_vel = pg.Vector2(0, 0)
        horizontal_vel = pg.Vector2(0, 0)
        if forward != 0:
            forward_vel = pg.Vector2(np.cos(self.angle), np.sin(self.angle)) * forward
        if horizontal != 0:
            horizontal_angle = self.angle+np.pi/2*horizontal
            horizontal_vel = pg.Vector2(np.cos(horizontal_angle), np.sin(horizontal_angle))
        vel = horizontal_vel+forward_vel
        if vel.length_squared() != 0.0:
            vel.normalize_ip()
        
        self.collider.set_velocity(vel * Player.SPEED)
        
        self.angle += self.angle_vel * Player.ROTATION_SPEED * dt
        if self.angle > np.pi:
            self.angle = -np.pi
        elif self.angle < -np.pi:
            self.angle = np.pi

        self.angles.push_value(self.angle)

    def update(self, dt, alpha):
        self.interpolated_angle = self.angles.get_interpolated(alpha)

    def get_angle(self) -> float:
        "Get the direction this player is looking at"
        return self.interpolated_angle
    
    def get_pos(self) -> pg.Vector2:
        return self.collider.get_interpolated_position()

def move_players(resources: Resources):
    input = resources[InputManager]

    for player in resources[EntityWorld].get_group(Player):
        player.angle_vel = input[InputAction.TurnRight]-input[InputAction.TurnLeft]
        player.forward_vel = input[InputAction.Forward]-input[InputAction.Backwards]
        player.horizontal_vel = input[InputAction.Right]-input[InputAction.Left]

def move_camera(resources: Resources):
    cam = resources[Camera3D]
    players = resources[EntityWorld].get_group(Player)
    if players:
        player = players[0]
        cam.set_pos(player.get_pos())
        cam.set_angle(player.get_angle())

class PlayerPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Update, move_players)
        app.add_systems(Schedule.PreDraw, move_camera)
