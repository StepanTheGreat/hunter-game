import pygame as pg
import moderngl as gl 

from plugin import Plugin, Resources, Schedule

from .player import Player

from modules.entity import EntityContainer, Entity

from core.assets import AssetManager

from ..render.sprite import SpriteContainer

class Sprite(Entity):
    HITBOX_SIZE = 12
    SPEED = 50

    def __init__(self, uid: int, pos: tuple[float, float], assets: AssetManager):
        super().__init__(uid)

        self.texture = assets.load(gl.Texture, "images/character.png")
        self.pos = pg.Vector2(*pos)
        self.vel = pg.Vector2(0, 0)
        
    def update(self, resources: Resources, dt: float):
        entities = resources[EntityContainer]
        if (players := entities.get_group(Player)):
            player = players[0]
            player_pos = player.get_pos()
            self.vel = (player_pos-self.pos)

            if self.vel.length_squared() != 0:
                self.vel.normalize_ip()

            self.pos += self.vel * Sprite.SPEED * dt


    def draw(self, resources: Resources):
        sprite_container = resources[SpriteContainer]

        sprite_container.push_sprite(
            self.texture,
            self.pos,
            pg.Vector2(48, 48)
        )
    
def spawn_sprite(resources: Resources):
    entities = resources[EntityContainer]
    

    for i in range(5):
        entities.push_entity(
            Sprite(entities.get_entity_uid(), (200*i, 0), resources[AssetManager])
        )

class SpritePlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Startup, spawn_sprite)