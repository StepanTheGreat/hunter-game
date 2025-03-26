import numpy as np

from plugin import *
from modules.tilemap import Tilemap
from core.collisions import CollisionWorld, StaticCollider

from typing import Union


TILE_SIZE = 48
# TILE_SIZE = 100

class WorldMap:
    "The globally explorable map"
    def __init__(
            self, 
            tilemap: Tilemap, 
            color_map: dict[int, Union[str, tuple]],
            transparent_tiles: set[int],
            collisions: CollisionWorld
        ):
        self.map = tilemap
        self.color_map = color_map
        self.transparent_tiles = transparent_tiles

        self.colliders = []
        self.create_map_colliders(collisions)

    def create_map_colliders(self, collisions: CollisionWorld):
        tiles = self.map.get_tiles()

        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                if tile == 0:
                    continue
                
                collider = StaticCollider(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                self.colliders.append(collider)
                collisions.add_collider(collider)
    
    def get_transparent_tiles(self) -> set[int]:
        """
        A transparent tiles set simply stores transparent tile IDs. 
        These are treated a bit differently when generating a map mesh, since their neighbour quads 
        don't get culled.
        """
        return self.transparent_tiles

    def get_color_map(self) -> dict[int, Union[str, tuple]]:
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
            ]),
            collisions = app.get_resource(CollisionWorld),
        ))