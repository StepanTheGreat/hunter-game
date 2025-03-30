import pygame as pg
import numpy as np

from plugin import Plugin, Resources, Schedule

from core.graphics import Camera3D
from core.entity import EntityWorld, Entity
from core.pg import Clock
from core.collisions import CollisionManager, DynCollider

class Player(Entity):
    HITBOX_SIZE = 14
    SPEED = 250
    ROTATION_SPEED = 3
    # The height of the camera
    CAMERA_HEIGHT = 24

    def __init__(self, uid: int, pos: tuple[float, float], collisions: CollisionManager):
        super().__init__(uid)

        self.collider = DynCollider(Player.HITBOX_SIZE, pos, 10)
        self.pos = self.collider.get_position_ptr()
        self.rect = pg.Rect(0, 0, Player.HITBOX_SIZE, Player.HITBOX_SIZE)
        self.vel = pg.Vector2(0, 0)
        self.angle = 0

        collisions.add_collider(self.collider)
        
    def update(self, dt: float):
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
        
        self.pos += vel * Player.SPEED * dt

        angle_vel = keys[pg.K_RIGHT]-keys[pg.K_LEFT]
        self.angle += angle_vel * Player.ROTATION_SPEED * dt
        if self.angle > np.pi:
            self.angle = -np.pi
        elif self.angle < -np.pi:
            self.angle = np.pi

    def get_angle(self) -> float:
        "Get the direction this player is looking at"
        return self.angle
    
    def get_pos(self) -> pg.Vector2:
        return self.pos.copy()
    
# def spawn_player(resources: Resources):
#     entities = resources[EntityWorld]
#     entities.push_entity(
#         Player(entities.get_entity_uid(), (0, 0), resources[CollisionManager])
#     )

def update_players(resources: Resources):
    dt = resources[Clock].get_delta()
    for player in resources[EntityWorld].get_group(Player):
        player.update(dt)

def move_camera(resources: Resources):
    players = resources[EntityWorld].get_group(Player)
    if len(players) > 0:
        player = players[0]
        cam = resources[Camera3D]
        cam.set_pos(player.get_pos())
        cam.set_angle(player.get_angle())

class PlayerPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Update, update_players)
        app.add_systems(Schedule.PreRender, move_camera)

