import pygame as pg
import moderngl as gl 

from plugin import Plugin, Resources, Schedule

from .player import Player

from plugins.collisions import DynCollider
from core.assets import AssetManager
from core.ecs import WorldECS, component

from plugins.components import *
from plugins.graphics.sprite import Sprite

from .projectile import ProjectileFactory
from .weapon import Weapon

@component
class Enemy:
    "An enemy tag"

ENEMY_PROJECTILE = ProjectileFactory(
    True,
    speed=800,
    radius=5,
    damage=20,
    lifetime=1.5,
    spawn_offset=0,
)

def make_enemy(pos: tuple[float, float], assets: AssetManager) -> tuple:
    texture = assets.load(gl.Texture, "images/character.png")
    return (
        Enemy(),
        Position(*pos),
        Angle(0.0),
        RenderPosition(*pos, 0),
        RenderAngle(0.0),
        Velocity(0, 0, 75),
        Sprite(texture, pg.Vector2(48, 48), (0, 0, 1, 1)),
        Team.enemy(),
        Hittable(),
        Weapon(ENEMY_PROJECTILE, 0.2, True),
        Health(300, 0.1),
        DynCollider(20, 3)
    )

def orient_enemy(resources: Resources):
    world = resources[WorldECS]

    players = list(world.query_component(Position, including=Player))
    if len(players) > 0:
        _, player_pos = players[0]
        
        for ent, (position, velocity, angle, weapon) in world.query_components(Position, Velocity, Angle, Weapon, including=Enemy):
            new_vel = (player_pos.get_position()-position.get_position())
            angle.set_angle(np.arctan2(new_vel.y, new_vel.x))            

            if new_vel.length_squared() != 0:
                new_vel.normalize_ip()

            velocity.set_velocity(new_vel.x, new_vel.y)

            if player_pos.get_position().distance_to(position.get_position()) < 500:
                weapon.start_shooting()
            else:
                weapon.stop_shooting()

def init_projectile_sprite(resources: Resources):
    assets = resources[AssetManager]

    ENEMY_PROJECTILE.user_components = (
        Sprite(
            assets.load(gl.Texture, "images/character.png"),
            pg.Vector2(16, 16),
            (0, 0, 1, 1)
        ),
    )
    
# def spawn_sprite(resources: Resources):
#     entities = resources[EntityWorld]

#     for i in range(5):
#         entities.push_entity(
#             Sprite(entities.get_entity_uid(), (200*i, 0), resources)
#         )

class EnemyPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Startup, init_projectile_sprite)
        app.add_systems(Schedule.FixedUpdate, orient_enemy)