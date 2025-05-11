from plugin import Plugin, Resources

from core.sound import SoundManager

from plugins.shared.events import ProjectileHitEvent
from plugins.server.components import *

def play_sound_on_projectile_hit(resources: Resources, event: ProjectileHitEvent):
    sounds = resources[SoundManager]

    sounds.play_soundpack("sounds/hit/hit.pck")   

class ProjectileSoundHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(ProjectileHitEvent, play_sound_on_projectile_hit)