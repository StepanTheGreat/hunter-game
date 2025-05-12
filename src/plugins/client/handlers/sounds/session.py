from plugin import Plugin, Resources

from core.sound import SoundManager

from plugins.client.commands import GameNotificationCommand, GameNotification
from plugins.server.components import *

def play_sound_on_lights_on(resources: Resources, command: GameNotificationCommand):
    sounds = resources[SoundManager]


    notification = command.notification
    if notification is GameNotification.LightsOn:
        sounds.play_sound("sounds/sirene.wav")

class SessionSoundHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(GameNotificationCommand, play_sound_on_lights_on)