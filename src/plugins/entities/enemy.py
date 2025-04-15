import pygame as pg
import moderngl as gl 

from plugin import Plugin, Resources, Schedule

from .player import Player

from plugins.collisions import DynCollider
from core.assets import AssetManager
from core.ecs import WorldECS, component

from plugins.components import *
from plugins.graphics.sprite import Sprite

@component
class Enemy:
    "An enemy tag"

# class Enemy(Entity):
#     HITBOX_SIZE = 16
#     SPEED = 120

#     def __init__(
#             self, 
#             pos: tuple[float, float], 
#             assets: AssetManager, 
#             collisions: CollisionManager,
#             sprites: SpriteRenderer,
#             player: Player = None,
#     ):
#         self.texture = assets.load(gl.Texture, "images/character.png")
#         self.sprite = Sprite(self.texture, pg.Vector2(pos), pg.Vector2(48, 48), (0, 0, 1, 1))
#         sprites.push_sprite(self.sprite)

#         self.collider = DynCollider(Enemy.HITBOX_SIZE, pos, 1)
#         self.player = player

#         self.vel = pg.Vector2(0, 0)

#         collisions.add_collider(self.collider)

#     def bind_player(self, player: Player):
#         self.player = player
        
#     def update_fixed(self, dt: float):
#         if self.player is not None:
#             player_pos = self.player.get_pos()
#             self.vel = (player_pos-self.collider.get_position())

#             if self.vel.length_squared() != 0:
#                 self.vel.normalize_ip()
            
#             self.collider.set_velocity(self.vel * Enemy.SPEED)

#     def update(self, dt, alpha):
#         self.sprite.position = self.get_pos()

#     def get_pos(self) -> pg.Vector2:
#         return self.collider.get_interpolated_position()

def make_enemy(pos: tuple[float, float], assets: AssetManager) -> tuple:
    texture = assets.load(gl.Texture, "images/character.png")
    return (
        Enemy(),
        Position(*pos),
        RenderPosition(*pos, 0),
        Velocity(0, 0, 75),
        Sprite(texture, pg.Vector2(48, 48), (0, 0, 1, 1)),
        DynCollider(40, 3)
    )

def orient_enemy(resources: Resources):
    world = resources[WorldECS]

    players = list(world.query_components(Player, Position))
    if len(players) > 0:
        player_ent, (_t, player_pos) = players[0]
        
        for ent, (_t, position, velocity) in world.query_components(Enemy, Position, Velocity):
            new_vel = (player_pos.get_position()-position.get_position())
            if new_vel.length_squared() != 0:
                new_vel.normalize_ip()

            velocity.set_velocity(new_vel.x, new_vel.y)
    
# def spawn_sprite(resources: Resources):
#     entities = resources[EntityWorld]

#     for i in range(5):
#         entities.push_entity(
#             Sprite(entities.get_entity_uid(), (200*i, 0), resources)
#         )

class EnemyPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.FixedUpdate, orient_enemy)