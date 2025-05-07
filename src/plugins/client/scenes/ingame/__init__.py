import numpy as np

from plugin import Plugin, Resources

from modules.scene import SceneBundle
from modules.tilemap import Tilemap

from plugins.shared.map import WorldMap, load_world_map, unload_world_map
from plugins.shared.components import reset_entity_uid_manager
from plugins.shared.network import clean_network_actors, Client

from plugins.server import ServerExecutor

from plugins.client.session import ServerTime

from .render.map import MapRendererPlugin
from .render.minimap import MinimapPlugin

from .gui import IngameGUI

TILE_SIZE = 48

def make_world_map() -> WorldMap:
    return WorldMap(
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
        tile_size=TILE_SIZE,
    )

class IngameScene(SceneBundle):
    def __init__(self, resources: Resources):
        super().__init__()

        self.add_auto_resources(
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

    def post_destroy(self, resources):
        # We need to close our client before leaving
        clean_network_actors(resources, Client)

        # If we're running a server - we're going to stop it as well
        server_executor = resources[ServerExecutor]
        if server_executor.is_running():
            server_executor.stop_server()

        # This is highly important, as reusing the same UID manager will lead to instabilities
        reset_entity_uid_manager(resources)

        # Reset and stop our server time
        resources[ServerTime].stop_and_reset()

class IngamePlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            MapRendererPlugin(),
            MinimapPlugin(),
        )