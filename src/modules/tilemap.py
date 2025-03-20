from typing import Optional
import numpy as np

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