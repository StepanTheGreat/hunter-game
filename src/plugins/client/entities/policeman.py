from plugin import Plugin, Resources, Schedule

from core.ecs import WorldECS, component
from core.assets import AssetManager
from core.graphics import Texture

from plugins.rpcs.client import SpawnPlayerCommand

from plugins.shared.entities.policeman import make_policeman, POLICEMAN_PROJECTILE, POLICEMAN_WEAPON_STATS
from plugins.shared.entities.weapon import Weapon

from plugins.client.graphics.lights import Light
from plugins.client.graphics.sprite import Sprite
from plugins.client.perspective import PerspectiveAttachment

from plugins.client.components import *

from .player import MainPlayer

CLIENT_POLICEMAN_PROJECTILE = POLICEMAN_PROJECTILE.copy()
CLIENT_POLICEMAN_PROJECTILE.user_components = (
    RenderPosition(24),
)
    
def make_client_policeman(
    uid: int, 
    pos: tuple[float, float], 
    ismain: bool,
    assets: AssetManager
) -> tuple:

    texture = assets.load(Texture, "images/sprites.atl#character")

    components = make_policeman(uid, pos) + (
        RenderPosition(24),
        Light((1, 1, 1), 20000, 1.2),
        Sprite(texture, (32, 64)),
        RenderAngle(),
        PerspectiveAttachment(24, 0-ismain),
        Weapon(CLIENT_POLICEMAN_PROJECTILE, POLICEMAN_WEAPON_STATS),
    )
    if ismain:
        components += (MainPlayer(), )
    else:
        components += (InterpolatedPosition(), )
    
    return components

def on_player_spawn_command(resources: Resources, command: SpawnPlayerCommand):
    "React to the spawn command"

    assets = resources[AssetManager]
    world = resources[WorldECS]

    world.create_entity(
        *make_client_policeman(command.uid, command.pos, command.is_main, assets)
    )

class ClientPolicemanPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(SpawnPlayerCommand, on_player_spawn_command)
