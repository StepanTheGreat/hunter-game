import pygame as pg
import math

ALMOST_ZERO = 10**-5

class TileMap:
    def __init__(self, width: int, height: int, tiles: list = None):
        self.width = width
        self.height = height
        self.transparent_tiles = set()
        # Generate an empty tileset
        if tiles is not None:
            assert len(tiles) == self.width
            assert len(tiles[0]) == self.height
            self.tiles = tiles 
        else:
            self.tiles = [[None for _ in range(width)] for _ in range(height)]

    def get_size(self) -> tuple[int, int]:
        return (self.width, self.height)
    
    def get_tiles(self) -> list:
        return self.tiles
    
    def add_transparent_tiles(self, *tiles: int):
        "A transparent tile is the one that allows the ray to continue passing through"
        for tile in tiles:
            self.transparent_tiles.add(tile)

    def is_transparent(self, tile: int) -> bool:
        return tile in self.transparent_tiles

class Caster:
    """
    A caster is an object that allows storing data, important for casting rays.

    """
    def __init__(
            self, 
            pos: pg.Vector2, 
            angle: float, 
            rays: int, 
            fov: int, 
            max_ray_distance: int
            ):
        self.pos = pos.copy() # The position is in tile coordinates 
        self.angle = angle
        self.fov = fov

        assert rays > 0
        self.rays = rays

        assert fov > 0
        self.fov = fov

        self.ray_gap = math.radians(self.fov/self.rays)

        assert max_ray_distance > 0
        self.max_ray_distance = max_ray_distance

    def set_pos(self, new_pos: pg.Vector2):
        self.pos = new_pos

    def set_angle(self, angle: float):
        self.angle = angle

def cast_rays(tilemap: TileMap, caster: Caster) -> list[list[(int, int, float, float, pg.Vector2, False)]]:
    """Cast a ray and return a list of results. A result is a tuple of: 
    ```
    (
        (tile_x, tile_y), 
        data (ID of the tile), 
        distance, 
        true_distance, 
        ray_hit_pos, 
        is_y_side
    )
    ```
    """
    caster_pos = caster.pos
    caster_angle = caster.angle

    tiles = tilemap.get_tiles()
    map_w, map_h = tilemap.get_size()

    results = []
    for ray in range(caster.rays):
        ray_angle = caster_angle-math.radians(caster.fov/2) + ray * caster.ray_gap
        ray_direction = pg.Vector2(math.cos(ray_angle), math.sin(ray_angle))
        
        # Here we calculate the hypothenuse for each axis.
        # Basically, to move by unit 1 (our grid cell size), how many "steps" do we need with our
        # axis direction?
        # The infinity here is used purely to avoid division by zero
        if ray_direction.x == 0:
            ray_direction.x = ALMOST_ZERO
        if ray_direction.y == 0:
            ray_direction.y = ALMOST_ZERO

        ray_step = pg.Vector2(
            math.sqrt(1 + (ray_direction.y / ray_direction.x) ** 2),
            math.sqrt(1 + (ray_direction.x / ray_direction.y) ** 2)
        )

        # A grid integer coordinate. We start with the player position
        # PS: int() for negative values produces a rounding for an opposed direction, which in turn
        # breaks this algorithm (i.e. 0.75 -> 0, while -0.75 -> 0).
        # math.floor will consistenly map the floating point to its lowest, even for negative values
        grid_x, grid_y = math.floor(caster_pos.x), math.floor(caster_pos.y)

        # A fixed integer grid vector direction, for traversing the grid
        grid_direction = (
            1 if ray_direction.x > 0 else -1,
            1 if ray_direction.y > 0 else -1
        )

        # Not a vector, but instead a 2 value map that allows us to compare 2 axis.
        # In DDA, we move and check the smallest axis, then increase its value.
        # 
        # Here we need to initialize it to the inner-cell position of the player (between 0 and 1),
        # to ensure that the ray doesn't start from the grid position, but from the player's.
        traversed_axis = pg.Vector2(0, 0)
        if ray_direction.x > 0:
            traversed_axis.x = (grid_x+1-caster_pos.x) * ray_step.x
        else:
            traversed_axis.x = (caster_pos.x-grid_x) * ray_step.x

        if ray_direction.y > 0:
            traversed_axis.y = (grid_y+1-caster_pos.y) * ray_step.y
        else:
            traversed_axis.y = (caster_pos.y-grid_y) * ray_step.y

        hit_stack = []
        ray_distance = 0
        y_side = False
        ignore_tile = None
        while ray_distance < caster.max_ray_distance:
            ray_distance = min(min(traversed_axis.x, traversed_axis.y), caster.max_ray_distance)
            if traversed_axis.x <= traversed_axis.y:
                y_side = False
                traversed_axis.x += ray_step.x
                grid_x += grid_direction[0]
            else:
                y_side = True
                traversed_axis.y += ray_step.y
                grid_y += grid_direction[1]

            if 0 <= grid_x < map_w and 0 <= grid_y < map_h:
                if (tile := tiles[grid_y][grid_x]) != None:
                    
                    if tile == ignore_tile:
                        continue

                    if ray_distance == 0:
                        ray_distance = ALMOST_ZERO

                    true_distance = ray_distance
                    ray_hit = caster_pos+ray_direction*ray_distance
                    ray_distance *= math.cos(ray_angle-caster_angle)

                    hit_stack.append((tile, ray_distance, true_distance, ray_hit, y_side, (grid_x, grid_y)))

                    if tilemap.is_transparent(tile):
                        ignore_tile = tile
                    else:
                        # We hit a static tile, time to stop
                        break
                else:
                    ignore_tile = None
        
        if hit_stack:
            results.append((ray, hit_stack))

    return results