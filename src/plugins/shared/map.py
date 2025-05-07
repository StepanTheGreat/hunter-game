from plugin import Plugin, Schedule, Resources, event, EventWriter

from core.ecs import WorldECS

from modules.tilemap import Tilemap

from .collisions import StaticCollider
from .components import Position

from typing import Union

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
            tile_size: float
        ):
        self.tile_size = tile_size
        self.map = tilemap
        self.color_map = color_map
        self.transparent_tiles = transparent_tiles

        self.colliders = []

    def destroy_map_colliders(self, world: WorldECS):
        "Remove all map colliders from the world"

        for collider_ent in self.colliders:
            world.remove_entity(collider_ent)

    def create_map_colliders(self, world: WorldECS):
        "Generate map colliders for this world map"

        tile_size = self.tile_size
        tiles = self.map.get_tiles()

        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                if tile == 0:
                    continue
                
                self.colliders.append(
                    world.create_entity(
                        Position(x*tile_size, y*tile_size),
                        StaticCollider(tile_size, tile_size)
                    )
                )
    
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
        
@event
class WorldMapLoadedEvent:
    "Fired when a world map gets loaded"

@event
class WorldMapUnloadedEvent:
    "Fired whenever a world map get unloaded"

def load_world_map(resources: Resources, wmap: WorldMap):
    """
    Load a new world map, and if a map is already present - clean it up and overwrite with the new one.
    This function will automatically create map colliders and push appropriate events.
    """

    unload_world_map(resources)

    # First we're going to insert all map's colliders
    wmap.create_map_colliders(resources[WorldECS])

    resources.insert(wmap)

    resources[EventWriter].push_event(WorldMapLoadedEvent())

def unload_world_map(resources: Resources):
    """
    Unload the current world map if present. This will automatically remove its 
    colliders and push appropriate events.
    """

    if WorldMap in resources:
        wmap = resources[WorldMap]
        wmap.destroy_map_colliders(resources[WorldECS])

        resources[EventWriter].push_event(WorldMapUnloadedEvent())