from core.ecs import WorldECS

from plugins.shared.events.map import *

from modules.tilemap import Tilemap

from plugins.shared.components import Position, StaticCollider, PlayerSpawnpoint, DiamondSpawnpoint, RobberSpawnpoint

WORLDMAP_JSON_SCHEMA = {
    "properties": {
        # The size of our map (amount of tiles in both X and Y axis)
     	"size": {"type": "integer", "minimum": 0},
        
        # The width of our wall in both X and Z axis
        "wall_width": {"type": "integer", "minimum": 1},

        # The height of our wall in Y axis
        "wall_height": {"type": "integer", "minimum": 1},

        # The tilemap of our walls. Essentially a 2D array of positive integers
        "wall_map": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {"type": "integer", "minimum": 0}, 
            }
        },

        # The tilemap for our floors, the same as `wall_map`
        "floor_map": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {"type": "integer", "minimum": 0}, 
            }
        },

        # The tilemap for our ceilings. Same thing
        "ceiling_map": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {"type": "integer", "minimum": 0}, 
            }
        },

        # Custom wall properties. This is a dictionary in which we can define custom walls and their
        # textures, if they're opaque or not and so on
        "wall_props": {
            "type": "object",

            # This rule only allows number keys (1, 2, 3, 4, ...),  BUT, disallowing 0, 1, 2 and 3, as
            # these are special tiles (spawnpoints on the map, each for different objects) 
            "propertyNames": {
                "pattern": "^(?![0-3]$)[0-9]+$"
            },

            # Every entry in this property map is an object, always containing the path to its 
            # texture (relative to the assets directory), and optionally an `opaque` boolean attribute.
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "texture": {"type": "string"},
                    "opaque": {"type": "boolean"}
                },
                "required": ["texture"]
            }
        },

        # Essentially the same thing, but for platforms (both floors and ceilings). This does mean
        # that they will share entries, but this shouldn't be a problem. Another thing is that
        # in this case, there's no restriction on key names, so you can easily use keys from 0 to infinity.
        #
        # As entry values, we expect texture paths. That's it.
        "platform_props": {
            "type": "object",
            "propertyNames": {
                "pattern": "^[0-9]+$"
            },
            "additionalProperties": {
                "type": "string",
            }
        },

        # We also require having a map scene camera. These will be used when there's no player
        # to attach to, so these will be the default "views" of the scene. It additionally acts
        # as a cheap way of implementing main-menus
        "map_camera": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"},
                "height": {"type": "number"},

                # The direction of the camera in degrees
                "angle": {"type": "number"}
            },
            "required": ["x", "y", "height", "angle"]
        }
    },

    # Well, a lot of these are required
    "required": [
        "size", 
        "wall_width", "wall_height", 
        "wall_map", "floor_map", "ceiling_map",
        "wall_props", "platform_props",
        "map_camera"
    ]
}
"""
## The worldmap format

A worldmap consists of 3 tilemap layers:
- The main tile layers (walls, windows, spawnpoints and much more)
- The floor 
- The ceiling

The main tile layer, while can contain additional tile definitions, by default has
these special values:
- 0: nothing (absence of anything)
- 1: policemen/player spawnpoint (should be at least the amount there are players)
- 2: robber spawnpoint (more = better)
- 3: diamond spawnpoint (should always be defined in play maps, but can be avoided in wait lobbies)

These values can't possibly be overwritten in a tileset and doing so will be met with an exception.
For any other case however, a worldmap defines 2 different tilesets, each with specific properties:
- main tile tileset (for tiles. Every tile definition there can have specific purpose, batching
modes, texture and so on)
- platform tileset (for floors/ceilings. Just contain texture definitions for these)

## Tiles
While it's pretty simple to understand platform tilesets, main tile tilesets are a bit more complex, as
they allow for more interactions:
- "type": the type of the tile. There are `tile` and `opaque_tile` (which is used for tiles that are 
supposed to be transparent like windows. They're defined separately for batching purposes).
- "texture": the texture used by this tile (the path relative to the `assets` directory)

## Objects
These are the things that bring life to the world. Isn't it boring to run around across dumb corridors
when everything you can look at are stupid blocks? Objects allow you to introduce your own 3D geometry
(3D models + textures) into the world at arbitrary positions, rotations and so on.
Objects while a nice addition, currently don't support collider definition, so consider defining
a separate collider separately.

First, you need to define an object in the `object_set` dictionary. Every object has its own key name:
- "texture": the texture this object is going to use by default (this can be overwritten)
- "model": the 3D model this object is going to use


Now when you would like to use an object, just add an object entry in the `objects` list:
{
    "id": `object_key`,
    "texture": `optional_texture_path`,
    "position": [x, y],
    "y": `height`,
    "rotation": `radians`
}

## Colliders
Currently, all scene colliders are defined in a separate `colliders` list, where every entry is a 
list of 4 values: `[x, y, w, h]`. You will need to define this for every object in the scene

## Lights
Finally, the most interesting part so far will be light. Lights as with colliders, are individual entries
in a global `lights` list. Every entry is: `[[x, y], h, [r, g, b], intensity]`, where `h` is a height of the light,
`r, g, b` is the color of said light and `intensity`... you get it. The scene at max can only define
a limited set of lights.
"""

PLAYER_SPAWNPOINT = 1
ROBBER_SPAWNPOINT = 2
DIAMOND_SPAWNPOINT = 3

class WallPropery:
    "The individual tile entry in the world map's tileset. Contains both its texture and if it's opaque"
    def __init__(self, texture: str, is_opaque: bool):
        self.texture = texture
        self.is_opaque = is_opaque

class MapCamera:
    "The map scene camera (when there are no players). Especially useful for game menus"

    def __init__(self, pos: tuple[float, float], height: float, angle: float):
        self.pos = pos
        self.height = height
        self.angle = angle

class WorldMap:
    def __init__(
        self,
        wall_map: Tilemap,
        floor_map: Tilemap,
        ceiling_map: Tilemap,
        wall_width: int,
        wall_height: int,

        wall_props: dict[int, WallPropery],
        platform_props: dict[int, str],
        map_camera: MapCamera
    ):
        # These maps should absolutely have the same dimensions
        assert wall_map.width == floor_map.width == ceiling_map.width
        assert wall_map.height == floor_map.height == ceiling_map.height

        self.wall_map = wall_map
        self.floor_map = floor_map
        self.ceiling_map = ceiling_map

        self.wall_width: int = wall_width
        self.wall_height: int = wall_height

        self.wall_props: dict[int, WallPropery] = wall_props
        self.platform_props: dict[int, str] = platform_props

        self.opaque_walls = self._get_opaque_walls()

        self.map_camera: MapCamera = map_camera

        self.map_entities = []

    def _get_opaque_walls(self) -> set[int]:
        "Returns all wall IDs that are opaque"

        return set(k for k, prop in self.wall_props.items() if prop.is_opaque)

    def destroy_map_entities(self, world: WorldECS):
        "Remove all map entities from the world (colliders and spawnpoints)"

        for ent in self.map_entities:
            world.remove_entity(ent)

    def create_map_entities(self, world: WorldECS):
        """
        Insert map entities in the ECS world. This procedure will insert these 2 types of entities:
        - colliders (collidable objects, map tiles)
        - spawnpoints (depending on the type of the spawnpoint)

        These are neccessary for
        """

        wall_size = self.wall_width
        tiles = self.wall_map.get_tiles()


        # This is just to reduce if/elif checks. We're not calling this method a lot, so we can afford this
        spawnpoint_cls_map = {
            1: PlayerSpawnpoint,
            2: RobberSpawnpoint,
            3: DiamondSpawnpoint
        }

        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):

                if tile == 0:
                    # If a tile is zero - do nothing
                    continue
                
                # Compute coordinates for our tile
                posx, posy = x*wall_size, y*wall_size

                if tile in spawnpoint_cls_map:
                    # If a tile is a spawnpoint tile - add it right in the center of the tile
                    self.map_entities.append(
                        world.create_entity(
                            Position(posx + wall_size/2, posy + wall_size/2),
                            spawnpoint_cls_map[tile]() # And here, we're initializing said spawnpoint component
                        )
                    )
                else:
                    # In any other case, we're adding a solid collider to the world
                    self.map_entities.append(
                        world.create_entity(
                            Position(posx, posy),
                            StaticCollider(wall_size, wall_size)
                        )
                    )
    
    def get_wall_prop(self, wall_id: int) -> WallPropery:
        "Get the wall properties of the given wall"

        return self.wall_props[wall_id]
    
    def get_opaque_walls(self) -> set[int]:
        "Return all opaque walls of this world map"

        return self.opaque_walls

    def get_platform_texture(self, plat_id: int) -> str:
        "Give the texture of the provided platform"

        return self.platform_props[plat_id]

    def get_wall_map(self) -> Tilemap:
        return self.wall_map
    
    def get_floor_map(self) -> Tilemap:
        return self.floor_map
    
    def get_ceiling_map(self) -> Tilemap:
        return self.ceiling_map
    
    def get_wall_size(self) -> tuple[int, int]:
        "Get the width and height dimensions of the world map's walls"

        return (self.wall_width, self.wall_height)
    
    def get_map_camera(self) -> MapCamera:
        return self.map_camera

'''
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
    
    def get_tile_size(self) -> int:
        return self.tile_size
'''