import pygame as pg
import moderngl as gl 

from plugin import Plugin, Resources, Schedule

from .player import Player

from core.entity import EntityWorld, Entity
from core.collisions import DynCollider, CollisionManager
from core.assets import AssetManager

from modules.inteprolation import Interpolated

from plugins.graphics import SpriteRenderer, LightManager, Light

class Sprite(Entity):
    HITBOX_SIZE = 16
    SPEED = 120

    def __init__(self, uid: int, pos: tuple[float, float], assets: AssetManager, collisions: CollisionManager):
        super().__init__(uid)

        self.texture = assets.load(gl.Texture, "images/character.png")

        self.collider = DynCollider(Sprite.HITBOX_SIZE, pos, 1)
        self.player_list = []

        self.vel = pg.Vector2(0, 0)

        collisions.add_collider(self.collider)

    def bind_player_list(self, player_list: list[Player]):
        """
        Bind this player list to the sprite so it can target players. 
        This is an essential operation, as without this method, the sprite wouldn't be able to find and 
        follow the player.
        """
        self.player_list = player_list
        
    def update_fixed(self, dt: float):
        if len(self.player_list) > 0:
            player = self.player_list[0]
            player_pos = player.get_pos()
            self.vel = (player_pos-self.collider.get_position())

            if self.vel.length_squared() != 0:
                self.vel.normalize_ip()
            
            self.collider.set_velocity(self.vel * Sprite.SPEED)

    def get_pos(self) -> pg.Vector2:
        return self.collider.get_interpolated_position()

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

def render_sprites(resources: Resources):
    entities = resources[EntityWorld]
    lighting = resources[LightManager]
    sprite_container = resources[SpriteRenderer]

    for sprite in entities.get_group(Sprite):
        sprite.draw(sprite_container)
        sprite_pos = sprite.get_pos()
        lighting.push_light(Light((sprite_pos.x, 48, -sprite_pos.y), (0.8, 0.8, 0.8)))

class SpritePlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Draw, render_sprites)