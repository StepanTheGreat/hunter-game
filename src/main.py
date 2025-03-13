import pygame as pg
import numpy as np
import moderngl as gl
import config

import math

TILE_SIZE = 32

FOV = 90
ASPECT_RATIO = config.H/config.W
ZFAR = 1024
ZNEAR = 0.1

VERTICIES = np.array([
    #pos          color
     0.0,   0.5,  1.0, 0.0, 0.0,
    -0.25, -0.5,  0.0, 1.0, 0.0,
     0.25, -0.5,  0.0, 0.0, 1.0 
], dtype=np.float32)

def load_str(path: str) -> str:
    contents = None
    with open(path, "r") as file:
        contents = file.read()
    return contents

SHADER_VERTEX = load_str("../shaders/main.vert")
SHADER_FRAGMENT = load_str("../shaders/main.frag")

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

    def draw(self):
        pass
        # pg.draw.circle(surface, (0, 255, 0), self.pos+MARGIN, Player.HITBOX_SIZE//2)
        # renderer.draw_color = (0, 255, 0, 255)
        # renderer.fill_rect(self.rect)
        # pg.draw.circle(surface, (0, 255, 0), self.pos, 2)


    def collide(self, rect: pg.Rect):
        if self.rect.colliderect(rect):
            self.pos = self.last_pos

    def get_angle(self) -> float:
        "Get the direction this player is looking at"
        return self.angle
    
    def get_pos(self) -> pg.Vector2:
        return pg.Vector2(self.pos)

screen = pg.display.set_mode((config.W, config.H), vsync=True, flags=pg.OPENGL | pg.DOUBLEBUF)
ctx = gl.get_context()
clock = pg.time.Clock()
quitted = False

zdiff = ZFAR-ZNEAR
f = 1/np.tan(FOV/2*2/np.pi)

projection = np.array([
	[f*ASPECT_RATIO, 0, 0, 0],
	[0, f, 0, 0],
	[0, 0, (ZFAR+ZNEAR)/zdiff, 1],
	[0, 0, -(2*ZFAR*ZNEAR)/zdiff, 0]
], dtype=np.float32)


# color_map[1] = load_texture(renderer, "images/window.png")
# color_map[2] = load_texture(renderer, "images/brick.jpg")
# color_map[3] = (200, 200, 120, 255)
# color_map[4] = (20, 200, 125, 255)

player = Player((10*TILE_SIZE, 10*TILE_SIZE))
# enemy = load_texture(renderer, "images/meteorite.png")
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

player_pos = player.get_pos()/TILE_SIZE

vbo = ctx.buffer(VERTICIES)

program = ctx.program(
    SHADER_VERTEX,
    SHADER_FRAGMENT,
)

vao = ctx.vertex_array(program, vbo, "position", "color")

while not quitted:
    dt = clock.tick(config.FPS) / 1000
    for event in pg.event.get():
        if event.type == pg.QUIT:
            quitted = True
    
    pg.display.set_caption(str(math.floor(clock.get_fps())))

    player.update(dt)
    for rect in tilemap_rects:
        player.collide(rect)

    ctx.clear(0, 0, 0, 1)
    vao.render(gl.TRIANGLES)
    
    pg.display.flip()

pg.quit()