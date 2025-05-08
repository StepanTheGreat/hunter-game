<<<<<<< HEAD
from plugin import Plugin, Resources

from core.ecs import WorldECS
from core.assets import AssetManager
=======
import numpy as np

from plugin import Plugin, Resources
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75

from modules.scene import SceneBundle
from modules.tilemap import Tilemap

<<<<<<< HEAD
from plugins.shared.map import WorldMap

from plugins.shared.network import clean_network_actors, Client
from plugins.server import ServerExecutor

from plugins.client.entities.policeman import make_client_policeman
from plugins.shared.components import reset_entity_uid_manager

from .render.map import *
from .render.minimap import *
=======
from plugins.shared.map import WorldMap, load_world_map, unload_world_map
from plugins.shared.components import reset_entity_uid_manager
from plugins.shared.network import clean_network_actors, Client

from plugins.server import ServerExecutor

from plugins.client.session import ServerTime

from .render.map import MapRendererPlugin
from .render.minimap import MinimapPlugin

>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
from .gui import IngameGUI

TILE_SIZE = 48

<<<<<<< HEAD
def make_world_map(resources: Resources, offset: tuple[float, float] = (0, 0)) -> tuple[WorldMap, MapModel]:
    world_map = WorldMap(
=======
def make_world_map() -> WorldMap:
    return WorldMap(
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
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
<<<<<<< HEAD
        world = resources[WorldECS],
        tile_size=TILE_SIZE,
        offset=offset
    )
    map_model = MapModel(resources, world_map)

    return world_map, map_model
=======
        tile_size=TILE_SIZE,
    )
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75

class IngameScene(SceneBundle):
    def __init__(self, resources: Resources):
        super().__init__()

        self.add_auto_resources(
<<<<<<< HEAD
            *make_world_map(resources, (0, 0)),
            IngameGUI(resources)
        )

=======
            IngameGUI(resources)
        )

    def pre_init(self, resources):
        # Before we're going to load this scene, we will load our world map first
        load_world_map(resources, make_world_map())

    def post_init(self, resources):
        # We're going to start the clock when the scene starts
        resources[ServerTime].start()

    def pre_destroy(self, resources):
        # Before destroying the scene, we would like to remove the world map
        unload_world_map(resources)

>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
    def post_destroy(self, resources):
        # We need to close our client before leaving
        clean_network_actors(resources, Client)

        # If we're running a server - we're going to stop it as well
        server_executor = resources[ServerExecutor]
        if server_executor.is_running():
            server_executor.stop_server()

        # This is highly important, as reusing the same UID manager will lead to instabilities
        reset_entity_uid_manager(resources)

<<<<<<< HEAD
=======
        # Reset and stop our server time
        resources[ServerTime].stop_and_reset()

>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
class IngamePlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            MapRendererPlugin(),
            MinimapPlugin(),
        )