import pygame as pg
import moderngl as gl 

from plugin import Plugin, Resources, Schedule

from .player import Player

from core.entity import EntityWorld, Entity
from core.collisions import DynCollider, CollisionManager
from core.assets import AssetManager
from core.pg import Clock

from plugins.graphics import SpriteRenderer

class Sprite(Entity):
    HITBOX_SIZE = 16
    SPEED = 60

    def __init__(self, uid: int, pos: tuple[float, float], assets: AssetManager, collisions: CollisionManager):
        super().__init__(uid)

        self.texture = assets.load(gl.Texture, "images/character.png")

        self.collider = DynCollider(Sprite.HITBOX_SIZE, pos, 1)
        self.pos = self.collider.get_position_ptr()
        self.vel = pg.Vector2(0, 0)

        collisions.add_collider(self.collider)
        
    def update(self, entities: EntityWorld, dt: float):
        if (players := entities.get_group(Player)):
            player = players[0]
            player_pos = player.get_pos()
            self.vel = (player_pos-self.pos)

            if self.vel.length_squared() != 0:
                self.vel.normalize_ip()

            self.pos += self.vel * Sprite.SPEED * dt


    def draw(self, renderer: SpriteRenderer):
        renderer.push_sprite(
            self.texture,
            self.pos,
            pg.Vector2(48, 48),
            (0, 0, 1, 1)
        )
    
# def spawn_sprite(resources: Resources):
#     entities = resources[EntityWorld]

#     for i in range(5):
#         entities.push_entity(
#             Sprite(entities.get_entity_uid(), (200*i, 0), resources)
#         )

def update_sprites(resources: Resources):
    entities = resources[EntityWorld]
    dt = resources[Clock].get_delta()

    for sprite in entities.get_group(Sprite):
        sprite.update(entities, dt)

def render_sprites(resources: Resources):
    entities = resources[EntityWorld]
    sprite_container = resources[SpriteRenderer]

    for sprite in entities.get_group(Sprite):
        sprite.draw(sprite_container)

class SpritePlugin(Plugin):
    def build(self, app):
        # app.add_systems(Schedule.Startup, spawn_sprite)
        app.add_systems(Schedule.Update, update_sprites)
        app.add_systems(Schedule.Draw, render_sprites)