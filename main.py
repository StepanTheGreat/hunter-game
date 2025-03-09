import pygame as pg
import config
import math

TILE_SIZE = 32

FOV = 90
RAYS = config.W//10
RAY_GAP = math.radians(FOV/RAYS)
RAY_DISTANCE = 20
WALL_HEIGHT = 15

COLOR_MAP = {
    1: (120, 120, 120),
    2: (200, 50, 50),
    3: (50, 200, 50),
    4: (50, 50, 200)
}

# A map that maps tiles to their (height, transparent)
TRANSPARENT_TILES = set([
    2
])

def clamp(value: int | float, mn: int|float, mx: int|float) -> int:
    return min(max(value, mn), mx)

class Player:
    HITBOX_SIZE = 12
    SPEED = 340
    ROTATION_SPEED = 4

    def __init__(self, pos: tuple[float, float]):
        self.last_pos = pg.Vector2(*pos)
        self.pos = pg.Vector2(*pos)
        self.rect = pg.Rect(0, 0, Player.HITBOX_SIZE, Player.HITBOX_SIZE)
        self.vel = pg.Vector2(0, 0)
        self.angle = 0
        
        self._sync_hitbox()

    def _sync_hitbox(self):
        "Syncronize the player's rect with its position. This function will also center the position of the hitbox"
        self.rect.center = self.pos

    def update(self, dt: float):
        keys = pg.key.get_pressed()
        forward = keys[pg.K_w]-keys[pg.K_s]
        left_right = keys[pg.K_d]-keys[pg.K_a]

        forward_vel = pg.Vector2(0, 0)
        left_right_vel = pg.Vector2(0, 0)
        if forward != 0:
            forward_vel = pg.Vector2(math.cos(self.angle), math.sin(self.angle)) * forward
        if left_right != 0:
            left_right_angle = self.angle+math.pi/2*left_right
            left_right_vel = pg.Vector2(math.cos(left_right_angle), math.sin(left_right_angle))
        vel = left_right_vel+forward_vel
        if vel.length_squared() != 0.0:
            vel.normalize_ip()

        new_pos = self.pos + vel * Player.SPEED * dt
        self.last_pos, self.pos = self.pos, new_pos
        self._sync_hitbox()

        angle_vel = keys[pg.K_RIGHT]-keys[pg.K_LEFT]
        self.angle += angle_vel * Player.ROTATION_SPEED * dt
        if self.angle > math.pi:
            self.angle = -math.pi
        elif self.angle < -math.pi:
            self.angle = math.pi

    def draw(self, surface: pg.Surface):
        pg.draw.circle(surface, (0, 255, 0), self.pos, Player.HITBOX_SIZE//2)

    def collide(self, rect: pg.Rect):
        if self.rect.colliderect(rect):
            self.pos = self.last_pos

    def get_angle(self) -> float:
        "Get the direction this player is looking at"
        return self.angle
    
    def get_pos(self) -> pg.Vector2:
        return pg.Vector2(self.pos)
 
pg.display.set_caption(config.CAPTION)

screen = pg.display.set_mode((config.W, config.H))
clock = pg.time.Clock()
quitted = False

player = Player((2*TILE_SIZE, 2*TILE_SIZE))
tiles = [
    [2, 2, 1, 2, 1, 1, 2, 2],
    [2, 0, 0, 0, 0, 0, 0, 2],
    [3, 0, 0, 2, 0, 0, 0, 2],
    [3, 0, 0, 4, 4, 4, 0, 2],
    [3, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 3],
    [3, 3, 2, 3, 2, 2, 3, 3]
]
tilemap_rect = pg.Rect(0, 0, len(tiles)*TILE_SIZE, len(tiles)*TILE_SIZE)
tilemap_rects = []
for y, row in enumerate(tiles):
    for x, tile in enumerate(row):
        if tile != 0:
            tilemap_rects.append(pg.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))

while not quitted:
    dt = clock.tick(config.FPS) / 1000
    for event in pg.event.get():
        if event.type == pg.QUIT:
            quitted = True

    player.update(dt)
    for rect in tilemap_rects:
        player.collide(rect)

    screen.fill((0, 0, 0))

    tilemap_size = (len(tiles)*TILE_SIZE, len(tiles)*TILE_SIZE)
    player_pos = player.get_pos()
    player_angle = player.get_angle()

    # The position of the player mapped to the grid
    player_grid_pos = pg.Vector2(
        player_pos.x/TILE_SIZE,
        player_pos.y/TILE_SIZE
    )
    # The position of the player inside a grid cell, from 0 to 1
    player_cell_pos = pg.Vector2(
        math.ceil(player_grid_pos.x)-player_grid_pos.x,
        math.ceil(player_grid_pos.y)-player_grid_pos.y,
    )

    rect_w = config.W//RAYS

    ray_angle = player_angle-math.radians(FOV/2)-RAY_GAP
    for ray in range(RAYS):
        ray_angle += RAY_GAP
        ray_angle = round(ray_angle, 4)
        ray_direction = pg.Vector2(math.cos(ray_angle), math.sin(ray_angle))
        
        # Here we calculate the hypothenuse for each axis.
        # Basically, to move by unit 1 (our grid cell size), how many "steps" do we need with our
        # axis direction?
        # The infinity here is used purely to avoid division by zero
        ray_step = pg.Vector2(
            abs(1 / ray_direction.x) if ray_direction.x != 0 else float('inf'),
            abs(1 / ray_direction.y) if ray_direction.y != 0 else float('inf')
        )

        # A grid integer coordinate. We start with the player position
        grid_pos = [int(player_grid_pos.x), int(player_grid_pos.y)]
        # A fixed integer grid vector direction, for traversing the grid
        grid_direction = (
            1 if ray_direction.x > 0 else -1,
            1 if ray_direction.y > 0 else -1
        )
        # Not a vector, but instead a 2 value map that allows us to compare 2 axis
        # In DDA, we move and check the smallest axis, then increase its value
        traversed_axis = pg.Vector2(0, 0)
        if ray_direction.x > 0:
            traversed_axis.x = (grid_pos[0]+1-player_grid_pos.x) * ray_step.x
        else:
            traversed_axis.x = (player_grid_pos.x-grid_pos[0]) * ray_step.x

        if ray_direction.y > 0:
            traversed_axis.y = (grid_pos[1]+1-player_grid_pos.y) * ray_step.y
        else:
            traversed_axis.y = (player_grid_pos.y-grid_pos[1]) * ray_step.y
        
        # A hit stack stores these values: (tile, distance)
        hit_stack = []
        ray_distance = 0
        while ray_distance < RAY_DISTANCE:
            ray_distance = min(min(traversed_axis.x, traversed_axis.y), RAY_DISTANCE)
            if traversed_axis.x <= traversed_axis.y:
                traversed_axis.x += ray_step.x
                grid_pos[0] += grid_direction[0]
            else:
                traversed_axis.y += ray_step.y
                grid_pos[1] += grid_direction[1]

            if 0 <= grid_pos[0] < len(tiles) and 0 <= grid_pos[1] < len(tiles):
                if (found_tile := tiles[grid_pos[1]][grid_pos[0]]) != 0:
                    hit_stack.append((found_tile, ray_distance))
                    if not (found_tile in TRANSPARENT_TILES):
                        break
        
        while hit_stack:
            tile, ray_distance = hit_stack.pop()

            # Fish-eye effect
            ray_distance *= math.cos(player_angle-ray_angle)

            tile_ray_distance = ray_distance*TILE_SIZE
            ray_hit = player_pos+ray_direction*tile_ray_distance
            
            dist = config.H/tile_ray_distance
            color = COLOR_MAP[tile]
            color = tuple([int(channel*(1-ray_distance/RAY_DISTANCE)) for channel in color])
            rect_h = int(dist*TILE_SIZE)
            # Rendering the rectangle
            pg.draw.rect(screen, color, (ray*rect_w, config.H//2-rect_h//2, rect_w, rect_h))

    for rect in tilemap_rects:
        pg.draw.rect(screen, (255, 255, 255), rect)
    player.draw(screen)

    pg.display.flip()

pg.quit()