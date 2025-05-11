from plugin import Plugin, Resources

from core.ecs import WorldECS, ComponentsRemovedEvent, ComponentsAddedEvent
from core.sound import SoundManager

from plugins.server.components import *

def play_sound_on_player_death(resources: Resources, event: ComponentsRemovedEvent):
    world = resources[WorldECS]
    sounds = resources[SoundManager]

    if Player in event.components and not world.contains_entity(event.entity):
        # Make sure that we only play this sound if this entity indeed was removed (not transformed)
        # and if it's a player

        sounds.play_soundpack("sounds/death/death.pck")

def play_sound_on_player_join(resources: Resources, event: ComponentsAddedEvent):
    sounds = resources[SoundManager]

    if Player in event.components and Robber not in event.components:
        # For some stupid reason I didn't make a separate ECS event for newly created entities, so
        # this is my lazy workaround. Because a robber transforms - it fires the components added
        # event as well, so we're checking against it 

        sounds.play_soundpack("sounds/join/join.pck")

class CharactersSoundHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(ComponentsRemovedEvent, play_sound_on_player_death)
        app.add_event_listener(ComponentsAddedEvent, play_sound_on_player_join)