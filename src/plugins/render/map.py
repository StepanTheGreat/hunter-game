"Map rendering"

import numpy as np
import moderngl as gl

from plugin import Resources, Plugin, Schedule

from ..map import WorldMap
from typing import Optional
from core.graphics import *
from core.assets import AssetManager

TILE_SIZE = 48

TILE_PIPELINE_PARAMS = PipelineParams(
    cull_face=True,
    depth_test=True,
    mode=gl.TRIANGLES
)

TILE_VERTEX_ATTRIBUTES = ("position", "color", "uv")

def gen_tile_mesh(
    coords: tuple[int, int], 
    size: float, 
    color: tuple[int, int, int],
    neighbours: tuple[bool, bool, bool, bool]
) -> Optional[MeshCPU]:
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

    mesh = MeshCPU(
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

def gen_map_models(ctx: gl.Context, assets: AssetManager, worldmap: WorldMap) -> tuple[list[tuple[gl.Texture, Model], Pipeline], ]:
    "Generate an array of renderable map models"

    def has_neighbour(tile: int, ntile: int, transparent_tiles: set[int]) -> bool:
        if tile in transparent_tiles:
            return ntile != 0
        else:
            return ntile != 0 and ntile not in transparent_tiles
    
    tilemap = worldmap.get_map()
    tiles = tilemap.get_tiles()

    color_map = worldmap.get_color_map()
    transparent_tiles = worldmap.get_transparent_tiles()

    white_texture = "white_texture"

    # A mesh group is a dictionary, where keys are textures, and values are meshes
    mesh_group: dict[gl.Texture, MeshCPU] = {}

    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if tile != 0:
                neighbours = tilemap.get_neighbours((x, y))
                neighbours = tuple(has_neighbour(tile, n, transparent_tiles) if n else False for n in neighbours)

                # A material is either a color or a texture path
                material = color_map[tile]

                color = (1, 1, 1) if type(material) is str else material
                texture = material if type(material) is str else white_texture

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

    pipeline = Pipeline(
        ctx, 
        assets.load(gl.Program, "shaders/base"), 
        TILE_PIPELINE_PARAMS, 
        TILE_VERTEX_ATTRIBUTES
    )
    models = []
    for group_texture_path, group_mesh in mesh_group.items():
        group_texture = assets.load(gl.Texture, group_texture_path)
        models.append((group_texture, Model(ctx, group_mesh, pipeline)))
    return models, pipeline
    

class MapModel:
    def __init__(self, ctx: gl.Context, assets: AssetManager, worldmap: WorldMap):
        models, pipeline = gen_map_models(ctx, assets, worldmap)
        self.models = models
        self.pipeline = pipeline

    def get_pipeline(self) -> Pipeline:
        return self.pipeline
    
    def get_models(self) -> list[tuple[gl.Texture, Model]]:
        return self.models

def create_map(resources: Resources):
    world_map = resources[WorldMap]
    gfx = resources[GraphicsContext]
    assets = resources[AssetManager]

    resources.insert(
        MapModel(gfx.get_context(), assets, world_map)
    )
    
def render_map(resources: Resources):
    if (map_renderer := resources.get(MapModel)) is None:
        return
    
    camera = resources[Camera3D]

    models, pipeline = map_renderer.get_models(), map_renderer.get_pipeline()
    pipeline["projection"] = camera.get_projection_matrix()
    pipeline["camera_pos"] = camera.get_camera_position()
    pipeline["camera_rot"] = camera.get_camera_rotation().flatten()

    pipeline["material"] = 0
    for texture, model in models:
        texture.use()
        model.render()

class MapRendererPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Startup, create_map)
        app.add_systems(Schedule.PostRender, render_map)