from typing import Union

from core.ecs import WorldECS

from plugins.collisions import StaticCollider
from .components import Position

from modules.tilemap import Tilemap

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
            world: WorldECS,
            tile_size: float,
            offset: tuple[int, int] = (0, 0)
        ):
        self.offset = offset
        # Offset is a grid vector from which the map's chunks should get either rendered or turned into colliders

        self.tile_size = tile_size
        self.map = tilemap
        self.color_map = color_map
        self.transparent_tiles = transparent_tiles

        self.colliders = []
        self.create_map_colliders(world)

    def create_map_colliders(self, world: WorldECS):

        tile_size = self.tile_size
        tiles = self.map.get_tiles()

        offsetx, offsety = self.offset

        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                if tile == 0:
                    continue
                
                posx, posy = offsetx+x, offsety+y
                self.colliders.append(
                    world.create_entity(
                        Position(posx*tile_size, posy*tile_size),
                        StaticCollider(tile_size, tile_size)
                    )
                )

    def get_offset(self) -> tuple[int, int]:
        return self.offset
    
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