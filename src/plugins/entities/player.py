import pygame as pg
import numpy as np

from plugin import Plugin, Resources, Schedule, event, EventWriter

from core.ecs import WorldECS, component
from core.input import InputManager
from plugins.graphics.lights import Light

from plugins.components import *

from .weapon import Weapon

class PlayerStats:
    "Stores global player related information. Useful for GUI and visualisations, since its a shared resource"
    def __init__(self):
        self.health: float = 0
        "Stores the player's health in percentages"

    def update_health(self, new_health: float):
        assert 0 <= new_health <= 1
        self.health = new_health

    def get_health(self) -> float:
        return self.health

class InputAction:
    Forward = "move_forward"
    Backwards = "move_backwards"
    Left = "move_left"
    Right = "move_right"

    TurnLeft = "turn_left"
    TurnRight = "turn_right"

    Shoot = "shoot"

@component
class Player:
    "A tag component that allows filtering out players"

@component
class MainPlayer:
    "A tag that allows distinguishing the current client from other clients"

@component
class PlayerController:
    """
    The state of the current player's input. This is used by 
    """
    def __init__(self):
        self.forward_dir = 0
        self.horizontal_dir = 0
        self.is_shooting = False

def control_player(resources: Resources):
    input = resources[InputManager]
    world = resources[WorldECS]
    ewriter = resources[EventWriter]

    for ent, (controller, angle_vel) in world.query_components(PlayerController, AngleVelocity, including=MainPlayer):
        angle_vel.set_velocity(input[InputAction.TurnRight]-input[InputAction.TurnLeft])
        controller.forward_dir = input[InputAction.Forward]-input[InputAction.Backwards]
        controller.horizontal_dir = input[InputAction.Right]-input[InputAction.Left]

        pos, vel = world.get_components(ent, Position, Velocity)

        ewriter.push_event(
            PlayerControlRequestEvent(pos.get_position(), vel.get_velocity())
        )

        break

def orient_player(resources: Resources):
    world = resources[WorldECS]

    for ent, (controller, vel, angle, weapon) in world.query_components(PlayerController, Velocity, Angle, Weapon):
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

def make_test_lights(resources: Resources):
    world = resources[WorldECS]

    for (x, y) in ((3*48, 5*48),):
        world.create_entity(
            Position(x, y),
            RenderPosition(x, y, 24),
            Light((0.3, 0.5, 1), 10000, 1)
        )

@event
class PlayerControlRequestEvent:
    "A request from the player to move its character"
    def __init__(self, pos: tuple[int, int], vel: tuple[float, float]):
        self.pos = pos
        self.vel = vel

class PlayerPlugin(Plugin):
    def build(self, app):
        app.insert_resource(PlayerStats())

        app.add_systems(Schedule.Startup, make_test_lights)
        app.add_systems(Schedule.Update, control_player)
        app.add_systems(Schedule.FixedUpdate, orient_player, priority=-1)
