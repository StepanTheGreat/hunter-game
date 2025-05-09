from plugin import Plugin, Schedule, Resources

from core.time import schedule_systems_seconds
from core.ecs import WorldECS
from core.input import InputManager

from ..actions import ClientActionDispatcher, ControlAction

from plugins.shared.components import *

class InputAction:
    Forward = "move_forward"
    Backwards = "move_backwards"
    Left = "move_left"
    Right = "move_right"

    TurnLeft = "turn_left"
    TurnRight = "turn_right"

    Shoot = "shoot"

def control_player(resources: Resources):
    input = resources[InputManager]
    world = resources[WorldECS]
    action_dispatcher = resources[ClientActionDispatcher]

    for ent, (controller, angle_vel) in world.query_components(PlayerController, AngleVelocity, including=MainPlayer):
        angle_vel.set_velocity(input[InputAction.TurnRight]-input[InputAction.TurnLeft])
        controller.forward_dir = input[InputAction.Forward]-input[InputAction.Backwards]
        controller.horizontal_dir = input[InputAction.Right]-input[InputAction.Left]

        controller.is_shooting = input[InputAction.Shoot]


        pos, vel, angle, angle_vel = world.get_components(ent, Position, Velocity, Angle, AngleVelocity)
        pos = pos.get_position()
        vel = vel.get_velocity()

        action_dispatcher.dispatch_action(ControlAction(
            (pos.x, pos.y), 
            (vel.x, vel.y), 
            angle.get_angle(), 
            angle_vel.get_velocity(),
            controller.is_shooting
        ))

        break

class SessionSystemsPlugin(Plugin):
    def build(self, app):
        schedule_systems_seconds(app, (control_player, 1/20, True))