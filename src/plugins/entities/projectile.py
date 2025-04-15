import pygame as pg
import numpy as np

from plugin import Plugin, Resources, Schedule

from core.ecs import WorldECS, component
from core.input import InputManager
from plugins.collisions import DynCollider, CollisionEvent, StaticCollider

from plugins.graphics.lights import Light

from plugins.components import *

@component
class Projectile:
    "A tag component that allows filtering out players"

@component
class DealsDamage:
    "Entities with this component can deal damage to entities with Hittable component"
    def __init__(self, damage: float):
        assert damage >= 0, "Can't deal negative damage"

        self.damage = damage

def make_projectile(
    is_enemy: bool, 
    pos: tuple[float, float], 
    direction: tuple[float, float], 
    lifetime: int
) -> tuple:
    return (
        Position(*pos),
        RenderPosition(*pos, 44),
        Velocity(*direction, 150),
        Light((1, 0.4, 0.4), 100),
        DynCollider(12, 30, sensor=True),
        DealsDamage(50),
        Temporary(lifetime),
        Team(is_enemy),
        Projectile()
    )

def deal_damage_on_collision(resources: Resources, event: CollisionEvent):
    world = resources[WorldECS]

    projectile_entity, target_entity = event.sensor_entity, event.hit_entity

    if not world.contains_entities(target_entity, projectile_entity):
        return

    # First we make sure that the sensor entity is a projectile
    if world.has_component(projectile_entity, Projectile):
        if event.hit_collider_ty is StaticCollider:
            # The projectile has hit a wall - kill him!
            world.remove_entity(projectile_entity)
        elif world.has_components(target_entity, Hittable, Team, Health):
            projectile_team, projectile_damage = world.get_components(projectile_entity, Team, DealsDamage)
            target_team, target_health = world.get_components(target_entity, Team, Health)

            # If they are on the same team however - we won't do anything
            if not projectile_team.same_team(target_team):
                target_health.hurt(projectile_damage.damage)

class ProjectilePlugin(Plugin):
    def build(self, app):
        app.add_event_listener(CollisionEvent, deal_damage_on_collision)