from plugin import Plugin, Resources

from core.sound import SoundManager

from plugins.shared.events import DiamondPickedUpEvent
from plugins.server.components import *

def play_sound_on_diamond_pickup(resources: Resources, _: DiamondPickedUpEvent):
    sounds = resources[SoundManager]

    sounds.play_soundpack("sounds/pickup/pickup.pck")   

class DiamondSoundHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(DiamondPickedUpEvent, play_sound_on_diamond_pickup)