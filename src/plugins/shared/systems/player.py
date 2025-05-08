import pygame as pg
import numpy as np

from plugin import Plugin, Resources, Schedule

from core.ecs import WorldECS
from plugins.shared.components import *

def orient_player_system(resources: Resources):
    world = resources[WorldECS]

    for _, (controller, vel, angle, weapon) in world.query_components(PlayerController, Velocity, Angle, Weapon):
        forward = controller.forward_dir
        horizontal = controller.horizontal_dir
        
        current_angle = angle.get_angle()

        forward_vel = pg.Vector2(0, 0)
        horizontal_vel = pg.Vector2(0, 0)
        if forward != 0:
            forward_vel = pg.Vector2(np.cos(current_angle), np.sin(current_angle)) * forward
        if horizontal != 0:
            horizontal_angle = current_angle+np.pi/2*horizontal
            horizontal_vel = pg.Vector2(np.cos(horizontal_angle), np.sin(horizontal_angle))

        new_vel = horizontal_vel+forward_vel
        if new_vel.length_squared() != 0.0:
            new_vel.normalize_ip()

        vel.set_velocity(new_vel.x, new_vel.y)

        if controller.is_shooting:
            weapon.start_shooting()
        else:
            weapon.stop_shooting()

class PlayerSystemsPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.FixedUpdate, orient_player_system, priority=-1)