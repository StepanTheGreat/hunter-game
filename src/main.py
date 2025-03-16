import pygame as pg
import numpy as np
import moderngl as gl
import config

import batch
from objects.player import Player
import math

TILE_SIZE = 48

FOV = 90
ASPECT_RATIO = config.H/config.W
ZFAR = 1024
ZNEAR = 0.1

def load_texture(ctx: gl.Context, path: str, color_channels: int = 4) -> gl.Texture:
    """
    Load an image and upload it to the GPU. It takes a gl context, image path and amount of color channels
    (default is 4) as arguments.
    """
    surf = pg.image.load(path)
    return ctx.texture(surf.get_size(), color_channels, surf.get_view("1"))

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

def gen_tile_geometry(
    coords: tuple[int, int], 
    size: float, 
    color: tuple[int, int, int],
    neighbours: tuple[bool, bool, bool, bool]
) -> tuple[np.ndarray, np.ndarray, int]:
    """ 
    This function generates geometry for a tile. It generates a tile mesh, constructs its verticies and
    generates an index buffer, both of which will be returned at the end of the call.

    ## Arguments:
        `coords`: x, y integer coordinates of the tile on the map (0, 0 is top-left)
        `size`: a floating point scalar to size the mesh
        `neighbours`: a 4-sized tuple of neighbours `[top, left, right, bottom]`. It's used to cull unused geometry, 
        so True means a neighbour exists, and False - it doesn't.

    This function will sacrifice useless verticies (4 tile corners) for the sake of conveniency.
    Theoretically this shouldn't be a serious problem since most culling should be done for the verticies outside,
    but this is simply a notice.
    """
    # The coordinates are topleft
    s = size
    x, y = coords
    x, y = x*s, y*s
    r, g, b = color
    top_neighbour, left_neighbour, right_neighbour, bottom_neighbour = neighbours

    quad_indices = lambda cind: np.array([cind, cind+1, cind+2, cind+1, cind+2, cind+3], dtype=np.uint32)

    # The incrementing index, that will be returned later
    verticies = np.array([], dtype=np.float32)
    indices = np.array([], dtype=np.uint32)
    current_index = 0

    if not top_neighbour:
        verticies = np.append(verticies, np.array([
            x,   s, y,        r, g, b,      0, 0,
            x+s, s, y,        r, g, b,      1, 0,
            x,   0, y,        r, g, b,      0, 1,
            x+s, 0, y,        r, g, b,      1, 1
        ], dtype=np.float32))
        indices = np.append(indices, quad_indices(current_index))
        current_index += 4

    if not bottom_neighbour:
        verticies = np.append(verticies, np.array([
            x,   s, y+s,    r, g, b,    0, 0,
            x+s, s, y+s,    r, g, b,    1, 0,
            x,   0, y+s,    r, g, b,    0, 1,
            x+s, 0, y+s,    r, g, b,    1, 1,
        ], dtype=np.float32))
        indices = np.append(indices, quad_indices(current_index))
        current_index += 4

    if not left_neighbour:
        verticies = np.append(verticies, np.array([
            x, s, y,        r, g, b,    0, 0,
            x, s, y+s,      r, g, b,    1, 0,
            x, 0, y,        r, g, b,    0, 1,
            x, 0, y+s,      r, g, b,    1, 1,
        ], dtype=np.float32))
        indices = np.append(indices, quad_indices(current_index))
        current_index += 4

    if not right_neighbour:
        verticies = np.append(verticies, np.array([
            x+s, s, y,      r, g, b,    0, 0,
            x+s, s, y+s,    r, g, b,    1, 0,
            x+s, 0, y,      r, g, b,    0, 1,
            x+s, 0, y+s,    r, g, b,    1, 1,
        ], dtype=np.float32))
        indices = np.append(indices, quad_indices(current_index))
        current_index += 4

    return verticies, indices


screen = pg.display.set_mode((config.W, config.H), vsync=True, flags=pg.OPENGL | pg.DOUBLEBUF)
ctx = gl.get_context()
clock = pg.time.Clock()
quitted = False

white_surf = pg.Surface((1, 1), pg.SRCALPHA)
white_surf.fill((255, 255, 255, 255))
white_texture = ctx.texture(white_surf.get_size(), 4, white_surf.get_view("1"))

color_map = {}
color_map[1] = load_texture(ctx, "../images/window.png")
color_map[2] = load_texture(ctx, "../images/brick.jpg", 3)
color_map[3] = (0.8, 0.8, 0.55)
color_map[4] = (0.12, 0.8, 0.6)

transparent_tiles = set([1])

color_map[1].filter = (gl.NEAREST, gl.NEAREST)
color_map[2].filter = (gl.NEAREST, gl.NEAREST)

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

pipeline = batch.Pipeline(
    ctx, 
    SHADER_VERTEX, SHADER_FRAGMENT, 
    ["position", "color", "uv"]
)

static_batcher = batch.StaticBatcher()
transparent_static_batcher = batch.StaticBatcher()

for y, row in enumerate(tiles):
    for x, tile in enumerate(row):
        if tile != 0:
            left_neighbour = (x > 0 and tiles[y][x-1] != 0)
            right_neighbour = (x < tiles_w-1 and tiles[y][x+1] != 0)
            top_neighbour = (y > 0 and tiles[y-1][x] != 0)
            bottom_neighbour = (y < tiles_h-1 and tiles[y+1][x] != 0)

            material = color_map[tile]

            color = (1, 1, 1) if type(material) is gl.Texture else material
            texture = material if type(material) is gl.Texture else white_texture 

            tile_verts, tile_inds = gen_tile_geometry(
                (x, y), 
                TILE_SIZE,
                color,
                [top_neighbour, left_neighbour, right_neighbour, bottom_neighbour]
            )

            if len(tile_verts) > 0 and len(tile_inds) > 0:
                batcher = transparent_static_batcher if tile in transparent_tiles else static_batcher
                batcher.push_geometry(
                    texture,
                    tile_verts,
                    tile_inds,
                    pipeline
                )

static_batcher.sync()
transparent_static_batcher.sync()

ctx.enable(gl.DEPTH_TEST)

ctx.enable(gl.SRC_ALPHA | gl.ONE_MINUS_SRC_ALPHA)

projection = perspective_matrix(ASPECT_RATIO, FOV, ZFAR, ZNEAR)
pipeline["projection"] = projection

while not quitted:
    dt = clock.tick(config.FPS) / 1000
    for event in pg.event.get():
        if event.type == pg.QUIT:
            quitted = True
    
    pg.display.set_caption(str(math.floor(clock.get_fps())))

    player.update(dt)
    # for rect in tilemap_rects:
    #     player.collide(rect)

    pipeline["camera_rot"] = player.camera_rotation().flatten()
    pipeline["camera_pos"] = player.camera_pos()

    ctx.clear(0, 0, 0, 1)

    pipeline["material"] = 0
    for group_texture, group in static_batcher.get_batches():
        group_texture.use()
        group.render(gl.TRIANGLES)
    
    pg.display.flip()

pg.quit()