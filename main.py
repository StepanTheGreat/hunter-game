import pygame as pg
import config, raycaster
import math

TILE_SIZE = 32

FOV = 90
RAYS = config.W//5
# RAYS = 10
RAY_GAP = math.radians(FOV/RAYS)
RAY_DISTANCE = 20
WALL_HEIGHT = 15

LINE_WIDTH = config.W//RAYS

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


minimap_surf = pg.Surface((config.W, config.H), pg.SRCALPHA)

player = Player((10*TILE_SIZE, 10*TILE_SIZE))
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
tiles = [[i if i != 0 else None for i in row] for row in tiles]

tilemap_rect = pg.Rect(0, 0, len(tiles)*TILE_SIZE, len(tiles)*TILE_SIZE)
tilemap_rects = []
for y, row in enumerate(tiles):
    for x, tile in enumerate(row):
        if tile is not None:
            tilemap_rects.append(pg.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))

tilemap = raycaster.TileMap(8, 8, tiles)
caster = raycaster.Caster(player.get_pos(), player.get_angle(), RAYS, FOV, RAY_DISTANCE)


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

    player_pos = player.get_pos()

    # The position of the player mapped to the grid.
    # This is stored as a float vector, since it's neccessary to later compute the player's inner-cell position
    # for the raycast
    player_grid_pos = pg.Vector2(
        player_pos.x/TILE_SIZE,
        player_pos.y/TILE_SIZE,
    )

    caster.set_pos(player_grid_pos)
    caster.set_angle(player.get_angle())
    raycast_results = raycaster.cast_ray(tilemap, caster)

    for (ray, tile, distance, ray_hit, is_y_side) in raycast_results:
        tile_ray_distance = distance*TILE_SIZE
        tile_ray_hit = ray_hit*tile_ray_distance
        
        dist = config.H/tile_ray_distance
        color = COLOR_MAP[tile]
        color = tuple([int(channel*(1-distance/RAY_DISTANCE)) for channel in color])
        if is_y_side:
            color = tuple([int(channel//2) for channel in color])
        rect_h = int(dist*TILE_SIZE)
        # Rendering the rectangle
        pg.draw.rect(screen, color, (ray*LINE_WIDTH, config.H//2-rect_h//2, LINE_WIDTH, rect_h))

    player.draw(minimap_surf)
    screen.blit(minimap_surf, (0, 0))

    pg.display.flip()

pg.quit()