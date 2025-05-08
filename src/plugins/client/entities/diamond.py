from plugin import Plugin, Resources, Schedule

from core.ecs import WorldECS
from core.assets import AssetManager
from core.graphics import Texture

from core.assets import AssetManager

from plugins.shared.entities.diamond import *
from plugins.client.components import *

from plugins.rpcs.client import SpawnDiamondsCommand

def make_client_diamond(uid: int, pos: tuple[int, int], assets: AssetManager):

    texture = assets.load(Texture, "images/sprites.atl#diamond")

    components = make_diamond(uid, pos)
    components += (
        RenderPosition(),
        Light(8, (1, 1, 1), 2000, 1.2),
        Sprite(0, texture, (16, 16)),
    )

    return components

def on_spawn_diamonds_command(resources: Resources, command: SpawnDiamondsCommand):
    "Spawn diamonds"

    world = resources[WorldECS]
    assets = resources[AssetManager]

    for (uid, pos) in command.diamonds:
        world.create_entity(
            *make_client_diamond(uid, pos, assets)
        )

class ClientDiamondPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(SpawnDiamondsCommand, on_spawn_diamonds_command)