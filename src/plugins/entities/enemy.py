import pygame as pg
import moderngl as gl 

from plugin import Plugin, Resources, Schedule

from .player import Player

from core.entity import Entity
from core.collisions import DynCollider, CollisionManager
from core.assets import AssetManager

from plugins.graphics import SpriteRenderer, Sprite

class Enemy(Entity):
    HITBOX_SIZE = 16
    SPEED = 120

    def __init__(
            self, 
            pos: tuple[float, float], 
            assets: AssetManager, 
            collisions: CollisionManager,
            sprites: SpriteRenderer,
            player: Player = None,
    ):
        self.texture = assets.load(gl.Texture, "images/character.png")
        self.sprite = Sprite(self.texture, pg.Vector2(pos), pg.Vector2(48, 48), (0, 0, 1, 1))
        sprites.push_sprite(self.sprite)

        self.collider = DynCollider(Enemy.HITBOX_SIZE, pos, 1)
        self.player = player

        self.vel = pg.Vector2(0, 0)

        collisions.add_collider(self.collider)

    def bind_player(self, player: Player):
        self.player = player
        
    def update_fixed(self, dt: float):
        if self.player is not None:
            player_pos = self.player.get_pos()
            self.vel = (player_pos-self.collider.get_position())

            if self.vel.length_squared() != 0:
                self.vel.normalize_ip()
            
            self.collider.set_velocity(self.vel * Enemy.SPEED)

    def update(self, dt, alpha):
        self.sprite.position = self.get_pos()

    def get_pos(self) -> pg.Vector2:
        return self.collider.get_interpolated_position()
    
# def spawn_sprite(resources: Resources):
#     entities = resources[EntityWorld]

#     for i in range(5):
#         entities.push_entity(
#             Sprite(entities.get_entity_uid(), (200*i, 0), resources)
#         )