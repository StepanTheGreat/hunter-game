import numpy as np
import pygame as pg

from plugin import Plugin

FOV = 90
ZFAR = 1024
ZNEAR = 0.1
ASPECT_RATIO = 748/540

HEIGHT = 24

def perspective_matrix(aspect_ratio: float, fov: float, zfar: float, znear: float) -> np.ndarray:
    "A perspective matrix generator"
    zdiff = zfar-znear
    f = 1/np.tan(fov/2*2/np.pi)
    return np.array([
        f*aspect_ratio, 0, 0, 0,
        0, f, 0, 0,
        0, 0, (zfar+znear)/zdiff, 1,
        0, 0, -(2*zfar*znear)/zdiff, 0
    ], dtype=np.float32)

class Camera3D:
    def __init__(self, aspect_ratio: float, fov: float, zfar: float, znear: float, pos: pg.Vector2, height: float):
        self.pos = pos
        self.height = height
        self.projection = perspective_matrix(aspect_ratio, fov, zfar, znear)
        self.angle = np.radians(30)

    def set_pos(self, new_pos: pg.Vector3):
        self.pos = new_pos

    def set_angle(self, new_angle: float):
        self.angle = new_angle

    def get_camera_position(self) -> np.ndarray:
        return np.array([self.pos.x, self.height, -self.pos.y], dtype=np.float32)
    
    def get_camera_rotation(self) -> np.ndarray:
        direction = pg.Vector3(-np.cos(self.angle), 0, -np.sin(self.angle))
        up = pg.Vector3(0, 1, 0)
        right = up.cross(direction)

        return np.array([
            [right.x, right.y, right.z],
            [up.x, up.y, up.z],
            [direction.x, direction.y, direction.z],
        ], dtype=np.float32)

    def get_projection_matrix(self) -> np.ndarray:
        return self.projection
    
class CameraPlugin(Plugin):
    def build(self, app):
        app.insert_resource(
            Camera3D(ASPECT_RATIO, FOV, ZFAR, ZNEAR, pg.Vector2(0, 0), HEIGHT)
        )

