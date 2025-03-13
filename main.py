import pygame as pg
import config

# from raycaster import TileMap, Caster, cast_rays
from bin.native import TileMap, Caster, cast_rays

import math

from pygame import _sdl2 as sdl2

TILE_SIZE = 32

FOV = 80
RAYS = config.W//1
# RAYS = 3

# assert config.W % RAYS == 0, "The screen width should be divisible by the number of rays"
# RAYS = 60
RAY_GAP = math.radians(FOV/RAYS)
RAY_DISTANCE = 20
WALL_HEIGHT = 15

LINE_WIDTH = config.W/RAYS

def clamp(value: int, mn: int, mx: int) -> int:
    return min(max(value, mn), mx)

def load_texture(renderer: sdl2.Renderer, path: str) -> sdl2.Texture:
    return sdl2.Texture.from_surface(renderer, pg.image.load(path))

class Player:
    HITBOX_SIZE = 12
    SPEED = 200
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

    def draw(self, renderer: sdl2.Renderer):
        # pg.draw.circle(surface, (0, 255, 0), self.pos+MARGIN, Player.HITBOX_SIZE//2)
        renderer.draw_color = (0, 255, 0, 255)
        renderer.fill_rect(self.rect)
        # pg.draw.circle(surface, (0, 255, 0), self.pos, 2)


    def collide(self, rect: pg.Rect):
        if self.rect.colliderect(rect):
            self.pos = self.last_pos

    def get_angle(self) -> float:
        "Get the direction this player is looking at"
        return self.angle
    
    def get_pos(self) -> pg.Vector2:
        return pg.Vector2(self.pos)
    
    def get_pos_tuple(self) -> tuple[float, float]:
        return (self.pos.x, self.pos.y)

window = sdl2.Window(config.CAPTION, (config.W, config.H))
renderer = sdl2.Renderer(window, 0, accelerated=True, vsync=True)

clock = pg.time.Clock()
cursor_grabbed = False
quitted = False

color_map = {}

color_map[1] = load_texture(renderer, "images/window.png")
color_map[2] = load_texture(renderer, "images/brick.jpg")
color_map[3] = (200, 200, 120, 255)
color_map[4] = (20, 200, 125, 255)

player = Player((10*TILE_SIZE, 10*TILE_SIZE))
enemy = load_texture(renderer, "images/meteorite.png")
enemy_pos = pg.Vector2(3*TILE_SIZE, 0)

tiles = [
    [1, 1, 0, 0, 0, 0, 2, 2],
    [2, 0, 0, 0, 0, 0, 0, 2],
    [3, 0, 0, 2, 0, 0, 0, 1],
    [1, 0, 0, 4, 1, 1, 0, 1],
    [3, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 3],
    [1, 3, 0, 0, 0, 0, 3, 3],
]

tilemap_rects = []
for y, row in enumerate(tiles):
    for x, tile in enumerate(row):
        if tile != 0:
            tilemap_rects.append(pg.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))

tilemap = TileMap(8, 8, tiles)

player_pos = player.get_pos()/TILE_SIZE
caster = Caster((player_pos.x, player_pos.y), player.get_angle(), RAYS, FOV, RAY_DISTANCE)

tilemap.add_transparent_tile(1)

def render_rays(raycast_results: list):
    draw_lines = 0
    for ray, hitstack in enumerate(raycast_results):
        for (tile, distance, ray_hit_x, ray_hit_y, is_y_side, _, _) in reversed(hitstack):
            tile_material = color_map[tile] 

            dist = config.H/distance
            rect_h = int(dist)

            if type(tile_material) == tuple:
                color = tile_material
                renderer.draw_color = color
                renderer.fill_rect((ray*LINE_WIDTH, config.H/2-rect_h/2, LINE_WIDTH, rect_h))
                draw_lines += 1
                # It's a color tile, simply fill it with color
            else:
                # Else it's a texture
                texture = tile_material

                # texture_region = get_mipmap_rect((texture.width, texture.height), rect_h)
                
                # This can be replaced with math.floor if neccessary
                texture_x = (ray_hit_x-int(ray_hit_x))*texture.width if is_y_side else (ray_hit_y-int(ray_hit_y))*texture.width
                
                # Texture rendering requires there to be enough rays to be able to draw the entire scene 
                # using 1-width stripes. If this isn't the case - the result will be highly blurry.
                # 
                # I'm not interpolating texture width here due to floating point and ray precision issues, 
                # which makes it extremely unreliable. I'm basically putting more rays to solve the problem in this case  
                renderer.blit(
                    texture, 
                    pg.Rect(ray*LINE_WIDTH, config.H/2-rect_h/2, LINE_WIDTH, rect_h), 
                    pg.Rect(texture_x, 0, 1, texture.height)
                )
                draw_lines += 1
    print(f"{draw_lines} draw lines!")

while not quitted:
    dt = clock.tick(config.FPS) / 1000
    for event in pg.event.get():
        if event.type == pg.QUIT:
            quitted = True
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                cursor_grabbed = not cursor_grabbed
                pg.mouse.set_visible(not cursor_grabbed)
        elif event.type == pg.MOUSEMOTION:
            if cursor_grabbed:
                pass
    
    window.title = str(math.floor(clock.get_fps()))

    if cursor_grabbed:
        pg.mouse.set_pos((config.W//2, config.H//2))

    player.update(dt)
    for rect in tilemap_rects:
        player.collide(rect)

    renderer.draw_color = (0, 0, 0, 255)
    renderer.clear()

    renderer.draw_color = (40, 40, 200, 255)
    renderer.fill_rect((0, 0, config.W, config.H//2))

    renderer.draw_color = (120, 120, 120, 255)
    renderer.fill_rect((0, config.H//2, config.W, config.H//2))


    player_pos = player.get_pos()

    # The position of the player mapped to the grid.
    # This is stored as a float vector, since it's neccessary to later compute the player's inner-cell position
    # for the raycast
    player_grid_pos = pg.Vector2(
        player_pos.x/TILE_SIZE,
        player_pos.y/TILE_SIZE,
    )

    caster.set_pos(player_grid_pos.x, player_grid_pos.y)
    caster.set_angle(player.get_angle())
    raycast_results = cast_rays(tilemap, caster)

    # Because the rays are given to us from the closest to the farthest, we will maintain a simple stack
    # that we will fill until no more rays appear.
    # If a different ray index appears - we draw from last to first all hit tiles, empty the stack, then set
    # the hitstack_ray to this new ray
    render_rays(raycast_results)

    renderer.draw_color = (255, 255, 255, 255)
    for rect in tilemap_rects:
        renderer.fill_rect((rect.x, rect.y, rect.w, rect.h))

    player.draw(renderer)

    renderer.present()

pg.quit()