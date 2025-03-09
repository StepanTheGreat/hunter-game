import pygame as pg
import config
import math

TILE_SIZE = 32

FOV = 90
RAYS = config.W//5
# RAYS = 10
ALMOST_ZERO = 10**-5
RAY_GAP = math.radians(FOV/RAYS)
RAY_DISTANCE = 20
WALL_HEIGHT = 15

TILEMAP_SIZE = 256

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

    def _clamp_position(self):
        self.pos.x = min(max(self.pos.x, 0), TILEMAP_SIZE*TILE_SIZE)
        self.pos.y = min(max(self.pos.y, 0), TILEMAP_SIZE*TILE_SIZE)

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
        # pg.draw.circle(surface, (0, 255, 0), self.pos+MARGIN, Player.HITBOX_SIZE//2)
        pg.draw.circle(surface, (0, 255, 0), self.pos, 2)


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

brick_texture = pg.image.load("brick.jpg").convert_alpha()

minimap_surf = pg.Surface((config.W, config.H), pg.SRCALPHA)

player = Player((-TILE_SIZE, -TILE_SIZE))
tiles = [
    [2, 2, 0, 0, 0, 0, 2, 2],
    [2, 0, 0, 0, 0, 0, 0, 2],
    [3, 0, 0, 2, 0, 0, 0, 2],
    [3, 0, 0, 4, 4, 4, 0, 2],
    [3, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 3],
    [3, 3, 0, 0, 0, 0, 3, 3],
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
    minimap_surf.fill((0, 0, 0, 0))

    for rect in tilemap_rects:
        pg.draw.rect(minimap_surf, (255, 255, 255), (rect.x, rect.y, rect.w, rect.h))

    tilemap_size = (len(tiles)*TILE_SIZE, len(tiles)*TILE_SIZE)
    player_pos = player.get_pos()
    player_angle = player.get_angle()

    # The position of the player mapped to the grid.
    # This is stored as a float vector, since it's neccessary to later compute the player's inner-cell position
    # for the raycast
    player_grid_pos = pg.Vector2(
        player_pos.x/TILE_SIZE,
        player_pos.y/TILE_SIZE,
    )

    rect_w = config.W//RAYS
    for ray in range(RAYS):
        ray_angle = player_angle-math.radians(FOV/2) + ray * RAY_GAP
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
        grid_x, grid_y = math.floor(player_grid_pos.x), math.floor(player_grid_pos.y)

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
            traversed_axis.x = (grid_x+1-player_grid_pos.x) * ray_step.x
        else:
            traversed_axis.x = (player_grid_pos.x-grid_x) * ray_step.x

        if ray_direction.y > 0:
            traversed_axis.y = (grid_y+1-player_grid_pos.y) * ray_step.y
        else:
            traversed_axis.y = (player_grid_pos.y-grid_y) * ray_step.y

        # A hit stack stores these values: (tile, distance)
        tile = None
        ray_distance = 0
        y_side = False
        while tile is None and 0 <= ray_distance < RAY_DISTANCE:
            ray_distance = min(min(traversed_axis.x, traversed_axis.y), RAY_DISTANCE)
            if traversed_axis.x <= traversed_axis.y:
                y_side = False
                traversed_axis.x += ray_step.x
                grid_x += grid_direction[0]
            else:
                y_side = True
                traversed_axis.y += ray_step.y
                grid_y += grid_direction[1]

            if 0 <= grid_x < len(tiles) and 0 <= grid_y < len(tiles):
                if (found_tile := tiles[grid_y][grid_x]) != 0:
                    tile = found_tile
        
        og_distance = ray_distance
        if tile is not None:
            # Fish-eye effect
            ray_distance *= math.cos(player_angle-ray_angle)

            # Honestly, this should panic, but this can happen if a player is stuck inside an object.
            # In this case, I think I'll keep it at a small amount instead
            if ray_distance == 0:
                ray_distance = ALMOST_ZERO

            tile_ray_distance = ray_distance*TILE_SIZE
            ray_hit = player_pos+ray_direction*tile_ray_distance
            
            dist = config.H/tile_ray_distance
            color = COLOR_MAP[tile]
            # color = tuple([int(channel*(1-ray_distance/RAY_DISTANCE)) for channel in color])
            if y_side:
                color = tuple([int(channel//2) for channel in color])
            rect_h = int(dist*TILE_SIZE)
            # Rendering the rectangle
            # screen.blit(brick_texture.subsurface())
            pg.draw.line(screen, (255, 0, 0), player_pos, ray_hit, 1)
            pg.draw.circle(screen, (0, 255, 0), ray_hit, 2)
            pg.draw.rect(screen, color, (ray*rect_w, config.H//2-rect_h//2, rect_w, rect_h))
            # tw, th = brick_texture.get_size()
            # cell_dist = math.ceil(og_distance)-og_distance
            # sub_texture = brick_texture.subsurface(cell_dist * tw, 0, min(int(cell_dist*tw)-1, int(cell_dist*tw)+5), th)
            # screen.blit(brick_texture, (ray*rect_w, config.H//2-rect_h//2))
        else:
            pg.draw.line(screen, (255, 0, 0), player_pos, player_pos + ray_direction*RAY_DISTANCE*TILE_SIZE, 1)

    player.draw(minimap_surf)
    screen.blit(minimap_surf, (0, 0))
    pg.display.flip()

pg.quit()