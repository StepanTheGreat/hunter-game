from plugin import Plugin, Resources

from core.ecs import WorldECS
from core.sound import SoundManager, Sound
from core.assets import AssetManager

from modules.scene import SceneBundle
from modules.tilemap import Tilemap

from plugins.shared.map import WorldMap

from plugins.shared.network import clean_network_actors
from plugins.server import ServerExecutor

from plugins.client.entities.policeman import make_client_policeman

from .render.map import *
from .render.minimap import *
from .gui import IngameGUI

TILE_SIZE = 48

def make_world_map(resources: Resources, offset: tuple[float, float] = (0, 0)) -> tuple[WorldMap, MapModel]:
    world_map = WorldMap(
        Tilemap(8, 8, np.array([
            [0, 0, 0, 0, 0, 0, 2, 2],
            [2, 1, 1, 0, 0, 0, 0, 2],
            [3, 0, 0, 2, 0, 0, 0, 1],
            [1, 0, 0, 4, 1, 1, 0, 1],
            [3, 0, 0, 0, 0, 0, 0, 2],
            [2, 0, 0, 0, 0, 0, 0, 2],
            [2, 0, 0, 2, 0, 0, 0, 3],
            [1, 3, 0, 0, 0, 0, 3, 3],
        ], dtype=np.uint32)),
        color_map = {
            1: "images/blocks.atl#window",
            2: "images/blocks.atl#cool_texture",
            3: (200, 200, 60),
            4: (30, 200, 170)
        },
        transparent_tiles = set([
            1
        ]),
        world = resources[WorldECS],
        tile_size=TILE_SIZE,
        offset=offset
    )
    map_model = MapModel(resources, world_map)

    return world_map, map_model

def spawn_entities(resources: Resources):
    world = resources[WorldECS]
    assets = resources[AssetManager]

    world.create_entity(*make_client_policeman(
        0,
        (0, 0),
        True,
        assets
    ))
    # world.create_entity(*make_player((0, 0)))

class IngameScene(SceneBundle):
    def __init__(self, resources: Resources):
        super().__init__()

        self.add_auto_resources(
            *make_world_map(resources, (0, 0)),
            IngameGUI(resources)
        )

    def post_init(self, resources):
        spawn_entities(resources)

        # resources[SoundManager].load_music("sounds/test_sound.ogg")
        # resources[SoundManager].play_music()

    def post_destroy(self, resources):
        # We need to close our client before leaving
        clean_network_actors(resources)

        # If we're running a server - we're going to stop it as well
        server_executor = resources[ServerExecutor]
        if server_executor.is_running():
            server_executor.stop_server()

class IngamePlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            MapRendererPlugin(),
            MinimapPlugin(),
        )