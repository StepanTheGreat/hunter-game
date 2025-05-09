from plugin import Plugin, Resources

from core.ecs import WorldECS
from core.assets import AssetManager

from core.assets import AssetManager

from plugins.client.entities import *
from plugins.client.components import *

from plugins.rpcs.client import SpawnDiamondsCommand

def on_spawn_diamonds_command(resources: Resources, command: SpawnDiamondsCommand):
    "Spawn diamonds"

    world = resources[WorldECS]
    assets = resources[AssetManager]

    for (uid, pos) in command.diamonds:
        world.create_entity(
            *make_client_diamond(uid, pos, assets)
        )

class DiamondHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(SpawnDiamondsCommand, on_spawn_diamonds_command)