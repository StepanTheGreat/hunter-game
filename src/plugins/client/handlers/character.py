from plugin import Plugin, Resources, EventWriter

from plugins.client.commands import CrookifyPolicemanCommand, SpawnPlayerCommand

from core.ecs import WorldECS, ComponentsRemovedEvent
from core.assets import AssetManager

from plugins.client.events import *
from plugins.client.entities import *
from plugins.shared.entities import crookify_policeman
from plugins.shared.services.uidman import EntityUIDManager

from plugins.client.components import *

def on_spawn_player_command(resources: Resources, command: SpawnPlayerCommand):
    "React to the spawn command"

    assets = resources[AssetManager]
    world = resources[WorldECS]

    world.create_entity(
        *make_client_policeman(command.uid, command.pos, command.is_main, assets)
    )

def _crookify_client_policeman(ewriter: EventWriter, world: WorldECS, ent: int, assets: AssetManager):
    "Crookify the policeman entity, but with additional client-side components"

    crookify_policeman(world, ent)

    world.remove_components(
        ent,
        Light, # A robber doesn't emit light, only cops do
        PerspectiveAttachment,
        Sprite,
        Weapon
    )

    is_main = world.has_component(ent, MainPlayer)
    texture = assets.load(Texture, "images/sprites.atl#robber")
    
    world.add_components(
        ent,

        # If the player is main, we would like to obviously prioritize its perspective, but if not - 
        # we shouldn't spectat the robber at all
        PerspectiveAttachment(28, (-1 if is_main else 1)),
        Sprite(0, texture, (48, 48)),
        Weapon(CLIENT_ROBBER_PROJECTILE, ROBBER_WEAPON_STATS)
    )

    if is_main:
        world.add_components(ent, Light(14, (0.9, 1, 0.9), 50000, 1.2))
        ewriter.push_event(MainPlayerIsACrookEvent())

def on_crookify_policeman_command(resources: Resources, command: CrookifyPolicemanCommand):
    "React on the crookify command by turning the specified policeman into a robber"

    world = resources[WorldECS]
    assets = resources[AssetManager]
    uidman = resources[EntityUIDManager]
    ewrtier = resources[EventWriter]

    ent = uidman.get_ent(command.uid)

    if ent is not None:
        _crookify_client_policeman(ewrtier, world, ent, assets)
    
def on_weapon_use_event(resources: Resources, event: WeaponUseEvent):
    """
    Listen for weapon use events and propagate them to the internal systems with more context
    (i.e. was it fired by the main player, or was it fired by a policeman or a robber)
    """

    world = resources[WorldECS]
    ewriter = resources[EventWriter]

    ent = event.ent

    if world.contains_entity(ent):
        is_policeman = world.has_component(ent, Policeman)
        is_main = world.has_component(ent, MainPlayer)
        ewriter.push_event(CharacterUsedWeaponEvent(is_policeman, is_main))

def on_main_player_death(resources: Resources, event: ComponentsRemovedEvent):
    "When the main player dies, we would like to push events notifying of that"

    if MainPlayer in event.components:
        resources[EventWriter].push_event(MainPlayerDiedEvent())

class CharacterHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(CrookifyPolicemanCommand, on_crookify_policeman_command)
        app.add_event_listener(SpawnPlayerCommand, on_spawn_player_command)

        app.add_event_listener(WeaponUseEvent, on_weapon_use_event)
        app.add_event_listener(ComponentsRemovedEvent, on_main_player_death)