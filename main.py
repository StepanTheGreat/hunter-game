import pygame as pg
import config
import math

TILE_SIZE = 64

FOV = 90
RAYS = 128
RAY_GAP = math.radians(FOV/RAYS)
RAY_DISTANCE = 700
FLOOR_Y = 0.80 # A fraction of the screen. It means that the floor starts at this percentage of the screen
WALL_HEIGHT = 10

COLOR_MAP = {
    1: (120, 120, 120),
    2: (200, 50, 50),
    3: (50, 200, 50),
    4: (50, 50, 200)
}

def clamp(value: int | float, mn: int|float, mx: int|float) -> int:
    return min(max(value, mn), mx)

class Player:
    HITBOX_SIZE = 16
    SPEED = 230
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
        pg.draw.rect(surface, (0, 255, 0), self.rect)

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

player = Player((255, 360))
tiles = [
    [1, 1, 0, 1, 0, 0, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 2],
    [3, 0, 0, 2, 0, 0, 0, 2],
    [3, 0, 0, 4, 4, 4, 0, 2],
    [3, 0, 0, 0, 0, 0, 0, 2],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 3],
    [1, 1, 0, 1, 0, 0, 3, 1]
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

    rect_w = config.W//RAYS

    for ray in range(RAYS):
        ray_angle = player_angle - math.radians(FOV)/2 + ray * RAY_GAP
        ray_direction = pg.Vector2(math.cos(ray_angle), math.sin(ray_angle))

        ray_distance = 0
        tile = None
        while ray_distance < RAY_DISTANCE:
            ray_pos = player_pos+ray_direction*ray_distance
            ray_pos = (int(ray_pos.x), int(ray_pos.y))
            ray_distance += 1
            if not tilemap_rect.collidepoint(ray_pos):
                continue
            found_tile = tiles[ray_pos[1]//TILE_SIZE][ray_pos[0]//TILE_SIZE]
            if found_tile != 0:
                tile = found_tile
                break

        if not tile: continue

        ray_distance *= math.cos(player_angle-ray_angle) # Fish-eye effect
        dist = config.H/ray_distance
        color = COLOR_MAP[tile]
        # color = tuple([channel*z for channel in color])
        rect_h = int(dist*WALL_HEIGHT)
        # pg.draw.line(screen, (255, 0, 0), player_pos, player_pos+ray_direction*ray_distance, 1)
        pg.draw.rect(screen, color, (ray*rect_w, config.H//2-rect_h//2, rect_w, rect_h))

    for rect in tilemap_rects:
        pg.draw.rect(screen, (255, 255, 255), rect)
    player.draw(screen)

    pg.display.flip()

pg.quit()