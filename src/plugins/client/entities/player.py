from plugin import Plugin, Resources, Schedule

from core.time import schedule_systems_seconds
from core.ecs import WorldECS
from core.input import InputManager

from plugins.rpcs.client import SyncHealthCommand

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

def on_new_main_player(resources: Resources, event: ComponentsAddedEvent):
    """
    This system runs every time a new main player is spawned, and its only purpose is to 
    reset the `HealthStats` global resource to 1.
    """
    
    if MainPlayer in event.components:
        resources[PlayerStats].update_health(1)

def on_sync_health_command(resources: Resources, command: SyncHealthCommand):
    world = resources[WorldECS]

    print("Got health sync command!")
    # When we receive this command, we would like to syncronize our health
    for _, health in world.query_component(Health, including=MainPlayer):
        health.set_percentage(command.health)

    # We're also going to update the `PlayerStats`, though I think this should probably
    # be done from a separate event listener instead
    resources[PlayerStats].update_health(command.health)

class ClientPlayerPlugin(Plugin):
    def build(self, app):
        app.insert_resource(PlayerStats())

        app.add_event_listener(ComponentsAddedEvent, on_new_main_player)
        app.add_event_listener(SyncHealthCommand, on_sync_health_command)

        schedule_systems_seconds(app, (control_player, 1/20, True))