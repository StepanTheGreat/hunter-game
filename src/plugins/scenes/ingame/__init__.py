from plugin import Plugin, Resources

from core.collisions import CollisionManager

from modules.scene import SceneBundle
from modules.tilemap import WorldMap, Tilemap

from .render.map import *
from .render.minimap import *

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
        collisions = resources[CollisionManager],
        tile_size=TILE_SIZE,
        offset=offset
    )
    map_model = MapModel(resources, world_map)

    return world_map, map_model

class IngameScene(SceneBundle):
    def __init__(self, resources: Resources):
        super().__init__(
            *make_world_map(resources, (0, 0)),
        )

class IngamePlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            MapRendererPlugin(),
            MinimapPlugin()
        )