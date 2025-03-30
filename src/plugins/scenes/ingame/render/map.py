"Map rendering"

import numpy as np
import moderngl as gl

from plugin import Resources, Plugin, Schedule, run_if, resource_exists

from modules.tilemap import WorldMap
from typing import Optional
from core.graphics import *
from plugins.graphics import ModelRenderer

from core.assets import AssetManager

TILE_SIZE = 48

def gen_tile_mesh(
    coords: tuple[int, int], 
    size: float, 
    color: tuple[int, int, int],
    neighbours: tuple[bool, bool, bool, bool]
) -> Optional[DumbMeshCPU]:
    """ 
    This function generates tile meshes, automatically culling faces based on neighbour information..

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

    mesh = DumbMeshCPU(
        np.array([], dtype=np.float32),
        np.array([], dtype=np.uint32)
    )

    if not top_neighbour:
        mesh.add_geometry(
            np.array([
                x,   s, y,        r, g, b,      0, 0,
                x+s, s, y,        r, g, b,      1, 0,
                x,   0, y,        r, g, b,      0, 1,
                x+s, 0, y,        r, g, b,      1, 1
            ], dtype=np.float32),
            np.array([0, 1, 2, 2, 1, 3], dtype=np.uint32)
        )

    if not bottom_neighbour:
        mesh.add_geometry(
            np.array([
                x,   s, y-s,    r, g, b,    0, 0,
                x+s, s, y-s,    r, g, b,    1, 0,
                x,   0, y-s,    r, g, b,    0, 1,
                x+s, 0, y-s,    r, g, b,    1, 1,
            ], dtype=np.float32),
            np.array([1, 0, 2, 1, 2, 3], dtype=np.uint32)
        )

    if not left_neighbour:
        mesh.add_geometry(
            np.array([
                x, s, y,        r, g, b,    0, 0,
                x, s, y-s,      r, g, b,    1, 0,
                x, 0, y,        r, g, b,    0, 1,
                x, 0, y-s,      r, g, b,    1, 1,
            ], dtype=np.float32),
            np.array([1, 0, 2, 1, 2, 3], dtype=np.uint32)
        )

    if not right_neighbour:
        mesh.add_geometry(
            np.array([
                x+s, s, y,      r, g, b,    0, 0,
                x+s, s, y-s,    r, g, b,    1, 0,
                x+s, 0, y,      r, g, b,    0, 1,
                x+s, 0, y-s,    r, g, b,    1, 1,
            ], dtype=np.float32),
            np.array([0, 1, 2, 2, 1, 3], dtype=np.uint32)
        )

    return mesh if not mesh.is_empty() else None 

def gen_map_models(
        gfx: GraphicsContext, 
        assets: AssetManager, 
        model_renderer: ModelRenderer,
        worldmap: WorldMap
    ) -> list[tuple[Model, gl.Texture]]:
    "Generate an array of renderable map models"

    def has_neighbour(tile: int, ntile: int, transparent_tiles: set[int]) -> bool:
        # This is a simple culling neighbour culling function.
        # Basically, we would like to check if a tile has a neighbour.
        #
        # If a tile is normal and it has a non-transparent neighbour - it does have a neighbour.
        # If a tile is normal and it has a transparent neighbour - it "doesn't"
        # If a tile is transparent and its neighbour isn't - it does have a neighbour 
        if tile in transparent_tiles:
            return ntile != 0
        else:
            return ntile != 0 and ntile not in transparent_tiles
    
    ctx = gfx.get_context()

    tilemap = worldmap.get_map()
    tiles = tilemap.get_tiles()

    color_map = worldmap.get_color_map()
    transparent_tiles = worldmap.get_transparent_tiles()

    # A mesh group is a dictionary, where keys are textures, and values are meshes
    mesh_group: dict[gl.Texture, DumbMeshCPU] = {}

    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if tile != 0:
                neighbours = tilemap.get_neighbours((x, y))
                neighbours = tuple(has_neighbour(tile, n, transparent_tiles) if n else False for n in neighbours)

                # A material is either a color or a texture path
                material = color_map[tile]

                color = (1, 1, 1) if type(material) is str else material
                texture = assets.load(gl.Texture, material) if type(material) is str else None

                tile_mesh = gen_tile_mesh(
                    (x, -y), 
                    TILE_SIZE,
                    color,
                    neighbours
                )

                if tile_mesh is not None:
                    if (group_mesh := mesh_group.get(texture)):
                        group_mesh.add_mesh(tile_mesh)
                    else:
                        mesh_group[texture] = tile_mesh

    pipeline = model_renderer.get_pipeline()
    models = [(Model(ctx, group_mesh, pipeline), group_texture) for group_texture, group_mesh in mesh_group.items()]
    return models
    
class MapModel:
    def __init__(
            self, 
            resources: Resources,
            world_map: WorldMap
        ):
        self.models = gen_map_models(
            resources[GraphicsContext], 
            resources[AssetManager], 
            resources[ModelRenderer], 
            world_map)

    def get_models(self) -> list[tuple[Model, gl.Texture]]:
        return self.models    

@run_if(resource_exists, MapModel)
def render_map(resources: Resources):
    map_model = resources[MapModel]
    renderer = resources[ModelRenderer]

    for model in map_model.get_models():
        renderer.push_model(*model)

class MapRendererPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.PostRender, render_map)