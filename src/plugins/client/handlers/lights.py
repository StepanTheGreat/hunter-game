from plugin import Plugin, Resources

from plugins.client.commands import GameNotificationCommand, ResetSceneLightsCommand

from plugins.client.services.graphics.lights import LightManager

from plugins.shared.interfaces.stage import GameNotification
from plugins.client.components import GameEntity

CLEAR_LIGHTING = (0.9, 0.9, 0.9)
NO_LIGHTING = (0.05, 0.1, 0.05)

def change_lighting_on_game_notification(resources: Resources, command: GameNotificationCommand):
    """
    When we receive a game notification, we analyze it and check if it means changing the current
    lights state of our manager. When the lights in the scene are on (the ambient color is light),
    all light sources should be disabled, as their lighting is redundant. When the ambient color
    is off (extremely dark) - lighting sources should be enabled back.
    """

    lights = resources[LightManager]

    notification = command.notification

    lights_enabled = not (notification is GameNotification.GameStarted)

    lights.set_ambient_color(CLEAR_LIGHTING if lights_enabled else NO_LIGHTING)
    lights.lights_enabled = not lights_enabled
    
def on_reset_lights_command(resources: Resources, _):
    lights = resources[LightManager]

    lights.set_ambient_color(CLEAR_LIGHTING)
    lights.lights_enabled = False

class LightsHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(GameNotificationCommand, change_lighting_on_game_notification)
        app.add_event_listener(ResetSceneLightsCommand, on_reset_lights_command)