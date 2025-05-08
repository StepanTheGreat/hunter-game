from plugin import Plugin, Resources, Schedule

from core.ecs import WorldECS, component
from core.assets import AssetManager
from core.graphics import Texture

from plugins.rpcs.client import SpawnPlayerCommand, CrookifyPolicemanCommand

from plugins.shared.entities.characters import *
from plugins.shared.services.uidman import EntityUIDManager

from plugins.client.components import *

from .player import MainPlayer

ROBBER_AMBIENT_LIGHT = (0.4, 0.8, 0.4)

CLIENT_ROBBER_PROJECTILE = ROBBER_PROJECTILE.copy()
CLIENT_ROBBER_PROJECTILE.user_components = (
    lambda: RenderPosition(),
)

CLIENT_POLICEMAN_PROJECTILE = POLICEMAN_PROJECTILE.copy()
CLIENT_POLICEMAN_PROJECTILE.user_components = (
    lambda: RenderPosition(),
)
    
def make_client_policeman(
    uid: int, 
    pos: tuple[float, float], 
    ismain: bool,
    assets: AssetManager
) -> tuple:

    texture = assets.load(Texture, "images/sprites.atl#character")

    components = make_policeman(uid, pos) + (
        RenderPosition(),
        Light(32, (1, 1, 1), 20000, 1.2),
        Sprite(0, texture, (32, 64)),
        RenderAngle(),
        PerspectiveAttachment(24, -1 if ismain else 0),
        Weapon(CLIENT_POLICEMAN_PROJECTILE, POLICEMAN_WEAPON_STATS),
    )
    if ismain:
        components += (MainPlayer(), )
    else:
        components += (InterpolatedPosition(), )
    
    return components

def crookify_client_policeman(world: WorldECS, ent: int, assets: AssetManager):
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
    texture = assets.load(Texture, "images/sprites.atl#meteorite")
    
    world.add_components(
        ent,

        # If the player is main, we would like to obviously prioritize its perspective, but if not - 
        # we shouldn't spectat the robber at all
        PerspectiveAttachment(28, (-1 if is_main else 1)),
        Sprite(0, texture, (38, 68)),
        Weapon(CLIENT_ROBBER_PROJECTILE, ROBBER_WEAPON_STATS)
    )

    if is_main:
        world.add_components(ent, Light(14, (0.9, 1, 0.9), 50000, 1.2))


def on_player_spawn_command(resources: Resources, command: SpawnPlayerCommand):
    "React to the spawn command"

    assets = resources[AssetManager]
    world = resources[WorldECS]

    world.create_entity(
        *make_client_policeman(command.uid, command.pos, command.is_main, assets)
    )

def on_crookify_policeman_command(resources: Resources, command: CrookifyPolicemanCommand):
    "React on the crookify command by turning the specified policeman into a robber"

    world = resources[WorldECS]
    assets = resources[AssetManager]
    uidman = resources[EntityUIDManager]

    ent = uidman.get_ent(command.uid)

    if ent is not None:
        crookify_client_policeman(world, ent, assets)

class ClientCharactersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(SpawnPlayerCommand, on_player_spawn_command)
        app.add_event_listener(CrookifyPolicemanCommand, on_crookify_policeman_command)
