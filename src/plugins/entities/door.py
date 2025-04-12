import pygame as pg
import moderngl as gl 

from plugin import Plugin, Resources, Schedule

from .player import Player

from core.entity import EntityWorld, Entity
from core.collisions import StaticCollider, CollisionManager
from core.assets import AssetManager

from modules.inteprolation import Interpolated

from plugins.graphics import SpriteRenderer, Sprite, LightManager, Light

class Door(Entity):
    HITBOX_SIZE = 24

    def __init__(
            self, 
            pos: tuple[float, float], 
            assets: AssetManager, 
            collisions: CollisionManager,
            sprites: SpriteRenderer
    ):
        self.texture = assets.load(gl.Texture, "images/character.png")
        self.sprite = Sprite(self.texture, pg.Vector2(pos), (48, 48), (0, 0, 1, 1))
        sprites.push_sprite(self.sprite)

        self.collider = StaticCollider(*pos, Door.HITBOX_SIZE, Door.HITBOX_SIZE)
        self.player_list = []

        collisions.add_collider(self.collider)

    def bind_player_list(self, player_list: list[Player]):
        """
        Bind this player list to the sprite so it can target players. 
        This is an essential operation, as without this method, the sprite wouldn't be able to find and 
        follow the player.
        """
        self.player_list = player_list

    def update(self, dt, alpha):
        pass
        
    def update_fixed(self, dt: float):
        pass

    def get_pos(self) -> pg.Vector2:
        return pg.Vector2(self.collider.rect.center)

    def draw(self, renderer: SpriteRenderer):
        renderer.push_sprite(
            self.texture,
            self.get_pos(),
            pg.Vector2(48, 48),
            (0, 0, 1, 1)
        )
    
# def spawn_sprite(resources: Resources):
#     entities = resources[EntityWorld]

#     for i in range(5):
#         entities.push_entity(
#             Sprite(entities.get_entity_uid(), (200*i, 0), resources)
#         )