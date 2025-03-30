from typing import Optional, Union
import numpy as np

from core.collisions import CollisionManager, StaticCollider

class Tilemap:
    "A tilemap container"
    def __init__(self, width: int, height: int, tiles: np.ndarray):
        self.width = width
        self.height = height

        assert tiles.shape == (width, height), "The tile array has to match provided width and height dimensions"
        assert tiles.dtype == np.uint32, "The tile array's type has to be uint32"

        self.tiles = tiles
    
    def set_tiles(self, new_tiles: np.ndarray):
        "Replace map's tiles with new ones"
        assert new_tiles.shape == (self.width, self.height), "The tile array has to match provided width and height dimensions"

    def get_size(self) -> tuple[int, int]:
        return (self.width, self.height)
    
    def get_tiles(self) -> np.ndarray:
        return self.tiles
    
    def get_tile(self, x: int, y: int) -> int:
        assert 0 <= x < self.width, "The x coordinate is off the grid"
        assert 0 <= y < self.height, "The y coordinate is off the grid"

        return self.tiles[y][x]
    
    def get_neighbours(self, tile: tuple[int, int]) -> tuple[Optional[int], Optional[int], Optional[int], Optional[int]]:
        """
        Get a tuple of tile's neighbours. It returns a 4 size tuple of [tile_top, tile_left, tile_right, tile_bottom].

        A neighbour is present if:
            1. Its coordinates are inside the grid
            2. Its value isn't 0
        """

        neighbours = [None, None, None, None]
        x, y = tile
        w, h = self.get_size()

        neighbour_pos = (
            (x, y-1), # up
            (x-1, y), # left
            (x+1, y), # right
            (x, y+1)  # down
        )
        for ind, (tx, ty) in enumerate(neighbour_pos):
            if (tx < 0 or tx >= w) or (ty < 0 or ty >= h):
                continue
            
            if (tile := self.get_tile(tx, ty)) != 0:
                neighbours[ind] = tile

        return tuple(neighbours)
    
class WorldMap:
    """
    The globally explorable map. Essentially it's the same as `Tilemap`, but has more details. 
    It contains tile information, colliders, materials and so on.
    """
    def __init__(
            self, 
            tilemap: Tilemap, 
            color_map: dict[int, Union[str, tuple]],
            transparent_tiles: set[int],
            collisions: CollisionManager,
            tile_size: float
        ):
        self.tile_size = tile_size
        self.map = tilemap
        self.color_map = color_map
        self.transparent_tiles = transparent_tiles

        self.colliders = []
        self.create_map_colliders(collisions)

    def create_map_colliders(self, collisions: CollisionManager):
        tile_size = self.tile_size
        tiles = self.map.get_tiles()

        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                if tile == 0:
                    continue
                
                collider = StaticCollider(x*tile_size, y*tile_size, tile_size, tile_size)
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