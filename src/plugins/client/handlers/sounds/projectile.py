from plugin import Plugin, Resources

from core.sound import SoundManager

from plugins.client.events import ProjectileHitEvent, CharacterUsedWeaponEvent 
from plugins.server.components import *

def play_sound_on_projectile_hit(resources: Resources, event: ProjectileHitEvent):
    sounds = resources[SoundManager]

    sounds.play_soundpack("sounds/hit/hit.pck")

def play_sound_on_projectile_shot(resources: Resources, event: CharacterUsedWeaponEvent):
    sounds = resources[SoundManager]

    sound = "sounds/gun/gun.pck" if event.is_policeman else "sounds/knife/knife.pck"
    sounds.play_soundpack(sound)

class ProjectileSoundHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(ProjectileHitEvent, play_sound_on_projectile_hit)
        app.add_event_listener(CharacterUsedWeaponEvent, play_sound_on_projectile_shot)