import numpy as np
import pygame as pg

from plugin import Plugin, Resources

from core.pg import WindowResizeEvent

from app_config import CONFIG

HEIGHT = 24

def perspective_matrix(aspect_ratio: float, fov: float, zfar: float, znear: float) -> np.ndarray:
    "A perspective matrix generator"
    zdiff = zfar-znear
    f = 1/np.tan(fov/2*2/np.pi)
    return np.array([
        f*aspect_ratio, 0,  0,                    0,
        0,              f,  0,                    0,
        0,              0,  (zfar+znear)/zdiff,   1,
        0,              0, -(2*zfar*znear)/zdiff, 0
    ], dtype=np.float32)

def othorgaphic_matrix(left: float, right: float, bottom: float, top: float, zfar: float, znear: float) -> np.ndarray:
    "An orthographic matrix generator"
    return np.array([
        2.0/(right-left),           0.0,                        0.0,                        0.0,
        0.0,                        2.0/(top-bottom),           0.0,                        0.0,
        0.0,                        0.0,                        -2.0/(zfar-znear),          0.0,
        -(right+left)/(right-left), -(top+bottom)/(top-bottom), -(zfar+znear)/(zfar-znear), 1.0,
    ], dtype=np.float32)

class Camera3D:
    FOV = 90
    ZFAR = 1024
    ZNEAR = 0.1

    def __init__(self, width: int, height: int, pos: pg.Vector2, y: float):
        self.pos = pos
        self.y = y
        self.projection = None
        self.angle = 0

        self.update_projection(width, height)

    def update_projection(self, new_width: int, new_height: int):
        "The same as with the `Camera2D`, this is supposed to get called every time the window's resolution has changed"
        self.projection = perspective_matrix(new_height/new_width, Camera3D.FOV, Camera3D.ZFAR, Camera3D.ZNEAR)

    def set_pos(self, new_pos: pg.Vector3):
        self.pos = new_pos

    def set_y(self, new_coordinate: float):
        self.y = new_coordinate

    def set_angle(self, new_angle: float):
        self.angle = new_angle

    def get_camera_position(self) -> np.ndarray:
        return np.array([self.pos.x, self.y, -self.pos.y], dtype=np.float32)
    
    def get_camera_rotation(self) -> np.ndarray:
        direction = pg.Vector3(-np.cos(self.angle), 0, -np.sin(self.angle))
        up = pg.Vector3(0, 1, 0)
        right = up.cross(direction)

        return np.array([
            [    right.x,     right.y,     right.z],
            [       up.x,        up.y,        up.z],
            [direction.x, direction.y, direction.z],
        ], dtype=np.float32)

    def get_projection_matrix(self) -> np.ndarray:
        return self.projection
    
class Camera2D:
    "Not a camera, but simply an orthographic projection matrix"
    ZFAR = -1
    ZNEAR = 1

    def __init__(self, width: int, height: int):
        self.projection = None
        self.update_projection(width, height)

    def update_projection(self, new_width: int, new_height: int):
        "Update this matrix with new window resolution in case it has changed"
        self.projection = othorgaphic_matrix(0, new_width, new_height, 0, Camera2D.ZFAR, Camera2D.ZNEAR)

    def get_projection_matrix(self) -> np.ndarray:
        return self.projection

def update_cameras(resources: Resources, event: WindowResizeEvent):
    resources[Camera2D].update_projection(event.new_width, event.new_height)
    resources[Camera3D].update_projection(event.new_width, event.new_height)
    
class CameraPlugin(Plugin):
    def build(self, app):
        app.insert_resource(
            Camera3D(CONFIG.width, CONFIG.height, pg.Vector2(0, 0), HEIGHT)
        )
        app.insert_resource(
            Camera2D(CONFIG.width, CONFIG.height)
        )
        app.add_event_listener(WindowResizeEvent, update_cameras)

