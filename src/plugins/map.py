from plugin import *
from modules.tilemap import Tilemap

import moderngl as gl
import numpy as np

TILE_SIZE = 48

class WorldMap:
    "The globally explorable map"
    def __init__(
            self, 
            tilemap: Tilemap, 
            color_map: dict[int, str | tuple[int, int, int, int]],
            transparent_tiles: set[int]
        ):
        self.map = tilemap
        self.color_map = color_map
        self.transparent_tiles = transparent_tiles
    
    def get_transparent_tiles(self) -> set[int]:
        """
        A transparent tiles set simply stores transparent tile IDs. 
        These are treated a bit differently when generating a map mesh, since their neighbour quads 
        don't get culled.
        """
        return self.transparent_tiles

    def get_color_map(self) -> dict[int, str | tuple[int, int, int, int]]:
        "A colormap is a tile ID to color/texture map that's used for mesh generation"
        return self.color_map

    def get_map(self) -> Tilemap:
        return self.map

class MapPlugin(Plugin):
    def build(self, app):
        app.insert_resource(WorldMap(
            Tilemap(8, 8, np.array([
                [0, 0, 0, 0, 0, 0, 2, 2],
                [2, 1, 1, 0, 0, 0, 0, 2],
                [3, 0, 0, 2, 0, 0, 0, 1],
                [1, 0, 0, 4, 1, 1, 0, 1],
                [3, 0, 0, 0, 0, 0, 0, 2],
                [2, 0, 0, 0, 0, 0, 0, 2],
                [2, 0, 0, 0, 0, 0, 0, 3],
                [1, 3, 0, 0, 0, 0, 3, 3],
            ], dtype=np.uint32)),
            color_map = {
                1: "images/window.png",
                2: "images/brick.jpg",
                3: (0.8, 0.8, 0.55),
                4: (0.12, 0.8, 0.6)
            },
            transparent_tiles = set([
                1
            ])
        ))
