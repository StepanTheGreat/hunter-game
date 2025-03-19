import pygame as pg
import numpy as np

from plugin import Plugin, Resources, Schedule
from . import Entity, EntityContainer

class Player(Entity):
    HITBOX_SIZE = 12
    SPEED = 250
    ROTATION_SPEED = 3
    # The height of the camera
    CAMERA_HEIGHT = 24

    def __init__(self, uid: int, pos: tuple[float, float]):
        super().__init__(uid)

        self.last_pos = pg.Vector2(*pos)
        self.pos = pg.Vector2(*pos)
        self.rect = pg.Rect(0, 0, Player.HITBOX_SIZE, Player.HITBOX_SIZE)
        self.vel = pg.Vector2(0, 0)
        self.angle = 0
        
        self._sync_hitbox()

    def _sync_hitbox(self):
        "Syncronize the player's rect with its position. This function will also center the position of the hitbox"
        self.rect.center = self.pos

    def update(self, dt: float, _):
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

        new_pos = self.pos + vel * Player.SPEED * dt
        self.last_pos, self.pos = self.pos, new_pos
        self._sync_hitbox()

        angle_vel = keys[pg.K_RIGHT]-keys[pg.K_LEFT]
        self.angle += angle_vel * Player.ROTATION_SPEED * dt
        if self.angle > np.pi:
            self.angle = -np.pi
        elif self.angle < -np.pi:
            self.angle = np.pi

    def draw(self, _):
        pass
        # pg.draw.circle(surface, (0, 255, 0), self.pos+MARGIN, Player.HITBOX_SIZE//2)
        # renderer.draw_color = (0, 255, 0, 255)
        # renderer.fill_rect(self.rect)
        # pg.draw.circle(surface, (0, 255, 0), self.pos, 2)


    def collide(self, rect: pg.Rect):
        if self.rect.colliderect(rect):
            self.pos = self.last_pos

    def get_angle(self) -> float:
        "Get the direction this player is looking at"
        return self.angle
    
    def get_pos(self) -> pg.Vector2:
        return self.pos.copy()

    def camera_rotation(self) -> np.ndarray:
        direction = pg.Vector3(-np.cos(self.angle), 0, -np.sin(self.angle))
        up = pg.Vector3(0, 1, 0)
        right = up.cross(direction)

        return np.array([
            [right.x, right.y, right.z],
            [up.x, up.y, up.z],
            [direction.x, direction.y, direction.z],
        ], dtype=np.float32)
    
    def camera_pos(self) -> np.ndarray:
        return np.array([self.pos.x, Player.CAMERA_HEIGHT, -self.pos.y])
    
def spawn_player(resources: Resources):
    entities = resources[EntityContainer]
    
    entities.push_entity(
        Player(entities.get_entity_uid(), (0, 0))
    )

class PlayerPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Startup, spawn_player)