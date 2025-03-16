import pygame as pg
import numpy as np
import moderngl as gl

import config

import batch
from objects.player import Player

@config.typed_dataclass
class AppConfig:
    width: int = 768
    height: int = 560
    fps: int = 60
    title: str = "Maze Runner"

try:
    conf = config.load_config_file(AppConfig, "../config.json")
except FileNotFoundError:
    conf = AppConfig()

TILE_SIZE = 48

FOV = 90
ASPECT_RATIO = conf.height/conf.width
ZFAR = 1024
ZNEAR = 0.1

T = TILE_SIZE
QUAD_VERTICIES = np.array([
    -0.5*T, T, 0,     0, 0,
     0.5*T, T, 0,     1, 0,
    -0.5*T, 0, 0,     0, 1,
     0.5*T, 0, 0,     1, 1
], dtype=np.float32)

QUAD_INDICES = np.array([0, 1, 2, 1, 3, 2], dtype=np.uint32)

def load_texture(ctx: gl.Context, path: str) -> gl.Texture:
    """
    Load an image and upload it to the GPU. It takes a gl context, image path and amount of color channels
    (default is 4) as arguments.
    """
    surf = pg.image.load(path)
    return ctx.texture(surf.get_size(), surf.get_bytesize(), surf.get_view("1"))

def load_str(path: str) -> str:
    contents = None
    with open(path, "r") as file:
        contents = file.read()
    return contents

SHADER_VERTEX = load_str("../shaders/main.vert")
SHADER_FRAGMENT = load_str("../shaders/main.frag")

SPRITE_SHADER_VERTEX = load_str("../shaders/sprite.vert")
SPRITE_SHADER_FRAGMENT = load_str("../shaders/sprite.frag")

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

    # The incrementing index, that will be returned later
    verticies = np.array([], dtype=np.float32)
    indices = np.array([], dtype=np.uint32)

    # current index
    cind = 0

    if not top_neighbour:
        verticies = np.append(verticies, np.array([
            x,   s, y,        r, g, b,      0, 0,
            x+s, s, y,        r, g, b,      1, 0,
            x,   0, y,        r, g, b,      0, 1,
            x+s, 0, y,        r, g, b,      1, 1
        ], dtype=np.float32))
        indices = np.append(indices, np.array([cind+1, cind, cind+2, cind+1, cind+2, cind+3], dtype=np.uint32))
        cind += 4

    if not bottom_neighbour:
        verticies = np.append(verticies, np.array([
            x,   s, y+s,    r, g, b,    0, 0,
            x+s, s, y+s,    r, g, b,    1, 0,
            x,   0, y+s,    r, g, b,    0, 1,
            x+s, 0, y+s,    r, g, b,    1, 1,
        ], dtype=np.float32))
        indices = np.append(indices, np.array([cind, cind+1, cind+2, cind+2, cind+1, cind+3], dtype=np.uint32))
        cind += 4

    if not left_neighbour:
        verticies = np.append(verticies, np.array([
            x, s, y,        r, g, b,    0, 0,
            x, s, y+s,      r, g, b,    1, 0,
            x, 0, y,        r, g, b,    0, 1,
            x, 0, y+s,      r, g, b,    1, 1,
        ], dtype=np.float32))
        indices = np.append(indices, np.array([cind, cind+1, cind+2, cind+2, cind+1, cind+3], dtype=np.uint32))
        cind += 4

    if not right_neighbour:
        verticies = np.append(verticies, np.array([
            x+s, s, y,      r, g, b,    0, 0,
            x+s, s, y+s,    r, g, b,    1, 0,
            x+s, 0, y,      r, g, b,    0, 1,
            x+s, 0, y+s,    r, g, b,    1, 1,
        ], dtype=np.float32))
        indices = np.append(indices, np.array([cind+1, cind, cind+2, cind+1, cind+2, cind+3], dtype=np.uint32))
        cind += 4

    return verticies, indices


screen = pg.display.set_mode((conf.width, conf.height), vsync=True, flags=pg.OPENGL | pg.DOUBLEBUF)
ctx = gl.get_context()
clock = pg.time.Clock()
quitted = False

white_surf = pg.Surface((1, 1), pg.SRCALPHA)
white_surf.fill((255, 255, 255, 255))
white_texture = ctx.texture(white_surf.get_size(), white_surf.get_bytesize(), white_surf.get_view("1"))

color_map = {}
color_map[1] = load_texture(ctx, "../images/window.png")
color_map[2] = load_texture(ctx, "../images/brick.jpg")
color_map[3] = (0.8, 0.8, 0.55)
color_map[4] = (0.12, 0.8, 0.6)

transparent_tiles = set([1])

color_map[1].filter = (gl.NEAREST, gl.NEAREST)
color_map[2].filter = (gl.NEAREST, gl.NEAREST)

player = Player((0, 0))

meteorite_texture = load_texture(ctx, "../images/character.png")
meteorite_pos = pg.Vector2(0, 0)

tiles_w, tiles_h = 8, 8
tiles = [
    [0, 0, 0, 0, 0, 0, 2, 2],
    [2, 1, 1, 0, 0, 0, 0, 2],
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
            tilemap_rects.append(pg.Rect(x*TILE_SIZE, -y*TILE_SIZE, TILE_SIZE, TILE_SIZE))

pipeline = batch.Pipeline(
    ctx, 
    SHADER_VERTEX, SHADER_FRAGMENT, 
    ["position", "color", "uv"]
)

static_batcher = batch.StaticBatcher()

def has_neighbour(tiles: list, tile_size: tuple[int, int], pos: tuple[int, int], tile: int) -> bool:
    w, h = tile_size
    x, y = pos

    if (x < 0 or x >= w) or (y < 0 or y >= h):
        # The neighbour is outside the grid, so it's not a neihgbour
        return False 
    
    # Neighbour tile
    ntile = tiles[y][x]

    if tile in transparent_tiles:
        return ntile != 0
    else:
        return ntile != 0 and ntile not in transparent_tiles

for y, row in enumerate(tiles):
    for x, tile in enumerate(row):
        if tile != 0:
            left_neighbour = has_neighbour(tiles, (tiles_w, tiles_h), (x-1, y), tile)
            right_neighbour = has_neighbour(tiles, (tiles_w, tiles_h), (x+1, y), tile)
            top_neighbour = has_neighbour(tiles, (tiles_w, tiles_h), (x, y-1), tile)
            bottom_neighbour = has_neighbour(tiles, (tiles_w, tiles_h), (x, y+1), tile)

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
                static_batcher.push_geometry(
                    texture,
                    tile_verts,
                    tile_inds,
                    pipeline
                )

static_batcher.sync()

sprite_program = ctx.program(SPRITE_SHADER_VERTEX, SPRITE_SHADER_FRAGMENT)
sprite_vbo = ctx.buffer(QUAD_VERTICIES)
sprite_ibo = ctx.buffer(QUAD_INDICES)
sprite_vao = ctx.vertex_array(sprite_program, sprite_vbo, "position", "uv", index_buffer=sprite_ibo)

ctx.enable(gl.DEPTH_TEST)
ctx.enable(gl.CULL_FACE)

ctx.enable(gl.SRC_ALPHA | gl.ONE_MINUS_SRC_ALPHA)

projection = perspective_matrix(ASPECT_RATIO, FOV, ZFAR, ZNEAR)

pipeline["material"] = 0
sprite_program["material"] = 0

pipeline["projection"] = projection
sprite_program["projection"] = projection

# An array of 3x3 matrices
sprite_rotations = np.zeros((256, 4), dtype=np.float32)
# An array of 2 axis vectors
sprite_positions = np.zeros((256, 2), dtype=np.float32)

while not quitted:
    dt = clock.tick(conf.fps) / 1000
    for event in pg.event.get():
        if event.type == pg.QUIT:
            quitted = True
    
    pg.display.set_caption(str(np.floor(clock.get_fps())))

    player.update(dt)
    # for rect in tilemap_rects:
    #     player.collide(rect)

    meteorite_angle = np.arctan2(meteorite_pos.x-player.pos.x, meteorite_pos.y-player.pos.y)
    meteorite_rot = np.array([
        [np.cos(meteorite_angle), -np.sin(meteorite_angle)],
        [np.sin(meteorite_angle), np.cos(meteorite_angle)]
    ], dtype=np.float32)

    player_camera_rot = player.camera_rotation().flatten()
    player_camera_pos = player.camera_pos()

    pipeline["camera_rot"] = player_camera_rot
    pipeline["camera_pos"] = player_camera_pos

    ctx.clear(0, 0, 0, 1)

    # Draw all our tiles
    for group_texture, group in static_batcher.get_batches():
        group_texture.use()
        group.render(gl.TRIANGLES)

    # Now draw sprites
    sprite_positions[0] = np.array([meteorite_pos.x, meteorite_pos.y], dtype=np.float32)
    sprite_rotations[0] = meteorite_rot.flatten()

    sprite_program["camera_rot"] = player_camera_rot
    sprite_program["camera_pos"] = player_camera_pos
    
    sprite_program["sprite_rot"] = sprite_rotations
    sprite_program["sprite_pos"] = sprite_positions

    meteorite_texture.use()
    sprite_vao.render(instances=1)
    
    pg.display.flip()

pg.quit()