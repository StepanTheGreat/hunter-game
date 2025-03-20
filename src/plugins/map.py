from plugin import *
from modules.tilemap import Tilemap

from core.graphics import GraphicsContext, Pipeline, StaticBatcher

import moderngl as gl
import numpy as np

TILE_SIZE = 48

def load_str(path: str) -> str:
    contents = None
    with open(path, "r") as file:
        contents = file.read()
    return contents

# SHADER_VERTEX = load_str("../shaders/main.vert")
# SHADER_FRAGMENT = load_str("../shaders/main.frag")

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
        indices = np.append(indices, np.array([cind, cind+1, cind+2, cind+2, cind+1, cind+3], dtype=np.uint32))
        cind += 4

    if not bottom_neighbour:
        verticies = np.append(verticies, np.array([
            x,   s, y-s,    r, g, b,    0, 0,
            x+s, s, y-s,    r, g, b,    1, 0,
            x,   0, y-s,    r, g, b,    0, 1,
            x+s, 0, y-s,    r, g, b,    1, 1,
        ], dtype=np.float32))
        indices = np.append(indices, np.array([cind+1, cind, cind+2, cind+1, cind+2, cind+3], dtype=np.uint32))
        cind += 4

    if not left_neighbour:
        verticies = np.append(verticies, np.array([
            x, s, y,        r, g, b,    0, 0,
            x, s, y-s,      r, g, b,    1, 0,
            x, 0, y,        r, g, b,    0, 1,
            x, 0, y-s,      r, g, b,    1, 1,
        ], dtype=np.float32))
        indices = np.append(indices, np.array([cind+1, cind, cind+2, cind+1, cind+2, cind+3], dtype=np.uint32))
        cind += 4

    if not right_neighbour:
        verticies = np.append(verticies, np.array([
            x+s, s, y,      r, g, b,    0, 0,
            x+s, s, y-s,    r, g, b,    1, 0,
            x+s, 0, y,      r, g, b,    0, 1,
            x+s, 0, y-s,    r, g, b,    1, 1,
        ], dtype=np.float32))
        indices = np.append(indices, np.array([cind, cind+1, cind+2, cind+2, cind+1, cind+3], dtype=np.uint32))
        cind += 4

    return verticies, indices

class WorldMap:
    "The globally explorable, renderable map"
    def __init__(
            self, 
            graphics: GraphicsContext, 
            tilemap: Tilemap, 
            colormap: dict[int, object],
            transparent_tiles: set[int]
        ):
        self.map = tilemap
        self.colormap = colormap
        self.transparent_tiles = transparent_tiles
        self.pipeline = Pipeline(SHADER_VERTEX, SHADER_FRAGMENT, ("position", "color", "uv"))
        self.static_batcher = self.__batch_map(graphics)
        self.static_batcher.sync()

    def __batch_map(self, graphics: GraphicsContext) -> StaticBatcher:
        batcher = StaticBatcher()

        ctx = graphics.get_context()
        white_texture = graphics.get_white_texture()

        w, h = self.map.get_size()
        for y, row in enumerate(self.map.get_tiles()):
            for x, tile in enumerate(row):
                if tile != 0:
                    neighbours = self.map.get_neighbours((x, y))

                    material = self.colormap[tile]

                    color = (1, 1, 1) if type(material) is gl.Texture else material
                    texture = material if type(material) is gl.Texture else white_texture 

                    tile_verts, tile_inds = gen_tile_geometry(
                        (x, -y), 
                        TILE_SIZE,
                        color,
                        neighbours
                    )

                    if len(tile_verts) > 0 and len(tile_inds) > 0:
                        batcher.push_geometry(
                            texture,
                            tile_verts,
                            tile_inds,
                            self.pipeline
                        )
        return batcher
    
    def get_transparent_tiles(self) -> set[int]:
        """
        A transparent tiles set simply stores transparent tile IDs. 
        These are treated a bit differently when generating a map mesh, since their neighbour quads 
        don't get culled.
        """
        return self.transparent_tiles

    def get_colormap(self) -> dict[int, object]:
        "A colormap is a tile ID to color/texture map that's used for mesh generation"
        return self.colormap

    def get_map(self) -> Tilemap:
        return self.map

    def render(self):
        self.pipeline["texture"] = 0
        for (texture, batch) in self.static_batcher.get_batches():
            texture.use()
            batch.render()

class MapPlugin(Plugin):
    def build(self, app):
        pass
        # app.insert_resource(WorldMap(
        #     Tilemap(8, 8, np.array([
        #         [0, 0, 0, 0, 0, 0, 2, 2],
        #         [2, 1, 1, 0, 0, 0, 0, 2],
        #         [3, 0, 0, 2, 0, 0, 0, 1],
        #         [1, 0, 0, 4, 1, 1, 0, 1],
        #         [3, 0, 0, 0, 0, 0, 0, 2],
        #         [2, 0, 0, 0, 0, 0, 0, 2],
        #         [2, 0, 0, 0, 0, 0, 0, 3],
        #         [1, 3, 0, 0, 0, 0, 3, 3],
        #     ], dtype=np.uint32))
        # ))
        # app.add_systems(Schedule.Render, render_map)

def render_map(resources: Resources):
    if (wmap := resources.get(WorldMap)):
        wmap.render()
        

