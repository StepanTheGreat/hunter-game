import pygame as pg
import moderngl as gl 

from core.entity import Entity
from core.collisions import StaticCollider, CollisionManager
from core.assets import AssetManager

from core.graphics import *

class Door(Entity):
    HITBOX_SIZE = 24

    def __init__(
            self, 
            pos: tuple[float, float], 
            assets: AssetManager, 
            collisions: CollisionManager,
    ):
        self.texture = assets.load(gl.Texture, "images/door.png")

        self.collider = StaticCollider(*pos, 48, 12)
        self.player_list = []

        collisions.add_collider(self.collider)

    def update(self, dt, alpha):
        pass
        
    def update_fixed(self, dt: float):
        pass

    def get_pos(self) -> pg.Vector2:
        return pg.Vector2(self.collider.rect.center)