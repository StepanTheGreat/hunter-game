import pygame as pg
import numpy as np

from plugin import Plugin, Resources, Schedule

from core.graphics import Camera3D
from modules.entity import EntityContainer, Entity
from modules.physics import make_ball_collider, ColliderType

from ..map import MapPhysicsWorld

class Player(Entity):
    HITBOX_SIZE = 20
    SPEED = 250
    ROTATION_SPEED = 3
    # The height of the camera
    CAMERA_HEIGHT = 24

    def __init__(self, uid: int, pos: tuple[float, float], resources: Resources):
        super().__init__(uid)

        self.last_pos = pg.Vector2(*pos)
        self.pos = pg.Vector2(*pos)
        self.rect = pg.Rect(0, 0, Player.HITBOX_SIZE, Player.HITBOX_SIZE)
        self.vel = pg.Vector2(0, 0)
        self.angle = 0

        self.collider = make_ball_collider(Player.HITBOX_SIZE, pos, ColliderType.Dynamic, 10)
        resources[MapPhysicsWorld].world.add_collider(self.collider)
        
    def update(self, resources: Resources, dt: float):
        keys = pg.key.get_pressed()
        forward = keys[pg.K_w]-keys[pg.K_s]
        left_right = keys[pg.K_d]-keys[pg.K_a]

        forward_vel = pg.Vector2(0, 0)
        left_right_vel = pg.Vector2(0, 0)
        if forward != 0:
            forward_vel = pg.Vector2(np.cos(self.angle), np.sin(self.angle)) * forward
        if left_right != 0:
            left_right_angle = self.angle+np.pi/2*left_right
            left_right_vel = pg.Vector2(np.cos(left_right_angle), np.sin(left_right_angle))
        vel = left_right_vel+forward_vel
        if vel.length_squared() != 0.0:
            vel.normalize_ip()
        
        self.pos = self.collider.get_position()
        self.collider.set_velocity(vel * Player.SPEED)

        angle_vel = keys[pg.K_RIGHT]-keys[pg.K_LEFT]
        self.angle += angle_vel * Player.ROTATION_SPEED * dt
        if self.angle > np.pi:
            self.angle = -np.pi
        elif self.angle < -np.pi:
            self.angle = np.pi

        cam = resources[Camera3D]
        cam.set_pos(self.get_pos())
        cam.set_angle(self.get_angle())

    def draw(self, _):
        pass

    def get_angle(self) -> float:
        "Get the direction this player is looking at"
        return self.angle
    
    def get_pos(self) -> pg.Vector2:
        return self.pos.copy()
    
def spawn_player(resources: Resources):
    entities = resources[EntityContainer]
    
    entities.push_entity(
        Player(entities.get_entity_uid(), (0, 0), resources)
    )

class PlayerPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Startup, spawn_player)