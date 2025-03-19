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