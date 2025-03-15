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
    #pos               color
    0.0,   0.5, 5,  1.0, 0.0, 0.0,
    -0.25, -0.5, 5,  0.0, 1.0, 0.0,
    0.25, -0.5, 5,  0.0, 0.0, 1.0 
], dtype=np.float32)

def load_str(path: str) -> str:
    contents = None
    with open(path, "r") as file:
        contents = file.read()
    return contents

SHADER_VERTEX = load_str("../shaders/main.vert")
SHADER_FRAGMENT = load_str("../shaders/main.frag")

def perspective_matrix(aspect_ratio: float, fov: float, zfar: float, znear: float) -> np.ndarray:
    zdiff = zfar-znear
    f = 1/np.tan(fov/2*2/np.pi)
    return np.array([
        f*aspect_ratio, 0, 0, 0,
        0, f, 0, 0,
        0, 0, (zfar+znear)/zdiff, 1,
        0, 0, -(2*zfar*znear)/zdiff, 0
    ], dtype=np.float32)

def rot_mat(x: int, y: int, z: int):
    "Generate a rotation matrix for 3 coordinates IN DEGREES (not radians)"
    # Convert degrees to radians
    x = np.radians(x)
    y = np.radians(y)
    z = np.radians(z)

    # Define X-axis rotation matrix
    rx = np.array([
        [1, 0, 0, 0],
        [0, np.cos(x), -np.sin(x), 0],
        [0, np.sin(x), np.cos(x), 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    # Define Y-axis rotation matrix
    ry = np.array([
        [np.cos(y), 0, np.sin(y), 0],
        [0, 1, 0, 0],
        [-np.sin(y), 0, np.cos(y), 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    # Define Z-axis rotation matrix
    rz = np.array([
        [np.cos(z), -np.sin(z), 0, 0],
        [np.sin(z), np.cos(z), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    return (rx @ ry @ rz)

def gen_tile_geometry(
    coords: tuple[int, int], 
    start_index: int, 
    size: float, 
    neighbours: tuple[bool, bool, bool, bool]
) -> tuple[np.ndarray, np.ndarray, int]:
    """ 
    This function generates geometry for a tile. It generates a tile mesh, constructs its verticies and
    generates an index buffer, both of which will be returned at the end of the call.

    ## Arguments:
        `coords`: x, y integer coordinates of the tile on the map (0, 0 is top-left)
        `start_index`: the starting indice for the index buffer
        `size`: a floating point scalar to size the mesh
        `neighbours`: a 4-sized tuple of neighbours `[top, left, right, bottom]`. It's used to cull unused geometry, 
        so True means a neighbour exists, and False - it doesn't.

    This function will sacrifice useless verticies (4 tile corners) for the sake of conveniency.
    Theoretically this shouldn't be a serious problem, since most culling should be done for the verticies outside,
    but this is simply a notice.
    """
    # The coordinates are topleft
    ind = start_index
    s = size
    x, y = coords
    x, y = x*s, y*s
    top_neighbour, left_neighbour, right_neighbour, bottom_neighbour = neighbours

    quad_indices = lambda cind: np.array([cind, cind+1, cind+2, cind+1, cind+2, cind+3], dtype=np.uint32)

    # The incrementing index, that will be returned later
    verticies = np.array([], dtype=np.float32)
    indices = np.array([], dtype=np.uint32)
    current_index = 0

    if not top_neighbour:
        verticies = np.append(verticies, np.array([
            x,   s, y,        1, 0, 0,
            x+s, s, y,        0, 1, 0,
            x,   0, y,        0, 0, 1,
            x+s, 0, y,        1, 0, 0
        ], dtype=np.float32))
        indices = np.append(indices, quad_indices(ind))
        current_index += 4

    if not bottom_neighbour:
        verticies = np.append(verticies, np.array([
            x,   s, y+s,    1, 0, 0,
            x+s, s, y+s,    0, 1, 0,
            x,   0, y+s,    0, 0, 1,
            x+s, 0, y+s,    1, 0, 0,
        ], dtype=np.float32))
        indices = np.append(indices, quad_indices(ind+current_index))
        current_index += 4

    if not left_neighbour:
        verticies = np.append(verticies, np.array([
            x, s, y,        1, 0, 0,
            x, s, y+s,      0, 1, 0,
            x, 0, y,        0, 0, 1,
            x, 0, y+s,      1, 0, 0,
        ], dtype=np.float32))
        indices = np.append(indices, quad_indices(ind+current_index))
        current_index += 4

    if not right_neighbour:
        verticies = np.append(verticies, np.array([
            x+s, s, y,      1, 0, 0,
            x+s, s, y+s,    0, 1, 0,
            x+s, 0, y,      0, 0, 1,
            x+s, 0, y+s,    1, 0, 0,
        ], dtype=np.float32))
        indices = np.append(indices, quad_indices(ind+current_index))
        current_index += 4

    print(indices)

    return verticies, indices, current_index


class Player:
    HITBOX_SIZE = 12
    SPEED = 250
    ROTATION_SPEED = 3

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

    def camera_rotation(self) -> np.ndarray:
        direction = pg.Vector3(-math.cos(self.angle), 0, -math.sin(self.angle))
        up = pg.Vector3(0, 1, 0)
        right = up.cross(direction)

        return np.array([
            [right.x, right.y, right.z],
            [up.x, up.y, up.z],
            [direction.x, direction.y, direction.z],
        ], dtype=np.float32)
    
    def camera_pos(self) -> np.ndarray:
        return np.array([self.pos.x, TILE_SIZE/2, -self.pos.y])

screen = pg.display.set_mode((config.W, config.H), vsync=True, flags=pg.OPENGL | pg.DOUBLEBUF)
ctx = gl.get_context()
clock = pg.time.Clock()
quitted = False

# color_map[1] = load_texture(renderer, "images/window.png")
# color_map[2] = load_texture(renderer, "images/brick.jpg")
# color_map[3] = (200, 200, 120, 255)
# color_map[4] = (20, 200, 125, 255)

player = Player((0, 0))
# enemy = load_texture(renderer, "images/meteorite.png")
enemy_pos = pg.Vector2(3*TILE_SIZE, 0)

tiles_w, tiles_h = 8, 8
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


tilemap_verticies = np.array([], dtype=np.float32)
tilemap_indices = np.array([], dtype=np.uint32)
current_index = 0

for y, row in enumerate(tiles):
    for x, tile in enumerate(row):
        if tile != 0:
            left_neighbour = (x > 0 and tiles[y][x-1] != 0)
            right_neighbour = (x < tiles_w-1 and tiles[y][x+1] != 0)
            top_neighbour = (y > 0 and tiles[y-1][x] != 0)
            bottom_neighbour = (y < tiles_h-1 and tiles[y+1][x] != 0)

            tile_verts, tile_inds, new_index = gen_tile_geometry(
                (x, y), 
                current_index, 
                TILE_SIZE,
                # [1, 1, 1, 1]
                [top_neighbour, left_neighbour, right_neighbour, bottom_neighbour]
            )
            current_index += new_index
            tilemap_verticies = np.append(tilemap_verticies, tile_verts)
            tilemap_indices = np.append(tilemap_indices, tile_inds)

vbo = ctx.buffer(tilemap_verticies)
ibo = ctx.buffer(tilemap_indices)

program = ctx.program(
    SHADER_VERTEX,
    SHADER_FRAGMENT,
)

ctx.enable(gl.DEPTH_TEST)

projection = perspective_matrix(ASPECT_RATIO, FOV, ZFAR, ZNEAR)
program["projection"] = projection

vao = ctx.vertex_array(program, vbo, "position", "color", index_buffer=ibo)

while not quitted:
    dt = clock.tick(config.FPS) / 1000
    for event in pg.event.get():
        if event.type == pg.QUIT:
            quitted = True
    
    pg.display.set_caption(str(math.floor(clock.get_fps())))

    player.update(dt)
    # for rect in tilemap_rects:
    #     player.collide(rect)

    program["camera_rot"] = player.camera_rotation().flatten()
    program["camera_pos"] = player.camera_pos()

    ctx.clear(0, 0, 0, 1)
    vao.render(gl.TRIANGLES)
    
    pg.display.flip()

pg.quit()