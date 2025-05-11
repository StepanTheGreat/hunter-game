from plugin import Plugin, Resources

from plugins.client.commands import GameNotificationCommand, ResetSceneLightsCommand

from core.ecs import WorldECS

from plugins.client.services.graphics.lights import LightManager

from plugins.shared.interfaces.stage import GameNotification
from plugins.client.components import GameEntity

CLEAR_LIGHTING = (0.9, 0.9, 0.9)
NO_LIGHTING = (0.05, 0.1, 0.05)

def on_game_notification(resources: Resources, command: GameNotificationCommand):
    "When the game is over, we would like to clean up ALL existing game entities"

    lights = resources[LightManager]

    notification = command.notification

    if notification is GameNotification.GameStarted:
        lights.set_ambient_color(NO_LIGHTING)
    else:
        lights.set_ambient_color(CLEAR_LIGHTING)
    
def on_reset_lights_command(resources: Resources, _):
    lights = resources[LightManager]

    lights.set_ambient_color(CLEAR_LIGHTING)

class LightsHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(GameNotificationCommand, on_game_notification)
        app.add_event_listener(ResetSceneLightsCommand, on_reset_lights_command)