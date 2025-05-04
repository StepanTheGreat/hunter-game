from plugin import Plugin, Resources, Schedule

from core.ecs import WorldECS
from core.input import InputManager

from ..actions import ClientActionDispatcher, ControlAction

from plugins.shared.components import *
from plugins.shared.entities.player import *

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

def control_player(resources: Resources):
    input = resources[InputManager]
    world = resources[WorldECS]
    action_dispatcher = resources[ClientActionDispatcher]

    for ent, (controller, angle_vel) in world.query_components(PlayerController, AngleVelocity, including=MainPlayer):
        angle_vel.set_velocity(input[InputAction.TurnRight]-input[InputAction.TurnLeft])
        controller.forward_dir = input[InputAction.Forward]-input[InputAction.Backwards]
        controller.horizontal_dir = input[InputAction.Right]-input[InputAction.Left]

        controller.is_shooting = input[InputAction.Shoot]


        pos, vel = world.get_components(ent, Position, Velocity)
        pos = pos.get_position()
        vel = vel.get_velocity()
        action_dispatcher.dispatch_action(
            ControlAction((pos.x, pos.y), (vel.x, vel.y))
        )

        break

class ClientPlayerPlugin(Plugin):
    def build(self, app):
        app.insert_resource(PlayerStats())
        app.add_systems(Schedule.FixedUpdate, control_player)
