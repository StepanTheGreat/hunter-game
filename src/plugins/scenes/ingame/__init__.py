from plugin import Plugin, Resources

from core.ecs import WorldECS
from core.sound import SoundManager, Sound
from core.assets import AssetManager

from modules.scene import SceneBundle
from modules.tilemap import Tilemap

from plugins.map import WorldMap
from plugins.network import Server, rpc, only_server, Listener

from plugins.entities.player import make_player
from plugins.entities.enemy import make_enemy

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
            1: "images/window.png",
            2: "images/cool_texture.png",
            3: (0.8, 0.8, 0.55),
            4: (0.12, 0.8, 0.6)
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

    world.create_entity(*make_player((0, 0)))

    for i in range(5):
        world.create_entity(*make_enemy((50*i, 0), assets))

class IngameScene(SceneBundle):
    def __init__(self, resources: Resources, is_server: bool):
        super().__init__()

        self.add_auto_resources(
            *make_world_map(resources, (0, 0)),
            IngameGUI(resources)
        )

    def post_init(self, resources):
        spawn_entities(resources)

        resources[SoundManager].load_music("sounds/test_sound.ogg")
        resources[SoundManager].play_music()

    def pre_destroy(self, resources):
        # We need to close our listener and server before leaving
        resources[Listener].close()
        if Server in resources:
            resources[Server].close()

class IngamePlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            MapRendererPlugin(),
            MinimapPlugin(),
        )