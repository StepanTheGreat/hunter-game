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

def make_enemy(pos: tuple[float, float], assets: AssetManager) -> tuple:
    texture = assets.load(gl.Texture, "images/character.png")
    return (
        Enemy(),
        Position(*pos),
        RenderPosition(*pos, 0),
        Velocity(0, 0, 75),
        Sprite(texture, pg.Vector2(48, 48), (0, 0, 1, 1)),
        Team.enemy(),
        Hittable(),
        Health(300),
        DynCollider(40, 3)
    )

def orient_enemy(resources: Resources):
    world = resources[WorldECS]

    players = list(world.query_component(Position, including=Player))
    if len(players) > 0:
        player_ent, player_pos = players[0]
        
        for ent, (position, velocity) in world.query_components(Position, Velocity, including=Enemy):
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