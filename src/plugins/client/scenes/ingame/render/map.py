"Map rendering"

import numpy as np
import moderngl as gl

from plugin import Resources, Plugin, Schedule, run_if, resource_exists

from typing import Optional

from plugins.shared.services.map import WorldMap
from plugins.client.events import WorldMapLoadedEvent, WorldMapUnloadedEvent

from plugins.client.graphics import ModelRenderer, VERTEX_GL_FORMAT, VERTEX_DTYPE

from core.graphics import *
from core.assets import AssetManager

TILE_SIZE = 48
FLOOR_COLOR = (30, 200, 30)
CEILING_COLOR = FLOOR_COLOR

def _bitcrush(x: float) -> float:
    return max(min(x * 128, 127), -128)

def normal(x: float, y: float, z: float):
    "Bit crush this normal's coordinates into byte range between -128 and 127"
    return _bitcrush(x), _bitcrush(y), _bitcrush(z)

def gen_tile_mesh(
    coords: tuple[int, int], 
    size: float, 
    color: tuple[int, int, int],
    uv_region: tuple[int, int, int],
    neighbours: tuple[bool, bool, bool, bool]
) -> Optional[DynamicMeshCPU]:
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
    top_neighbour, left_neighbour, right_neighbour, bottom_neighbour = neighbours

    uvx, uvy, uvw, uvh = uv_region
    uvw, uvh = uvx+uvw, uvy+uvh

    mesh = DynamicMeshCPU(
        np.array([], dtype=VERTEX_DTYPE),
        np.array([], dtype=np.uint32),
        vertex_dtype=VERTEX_DTYPE
    )

    if not top_neighbour:
        mesh.add_geometry(
            np.array([
                ((x,   s, y),  normal(0, 0, -1),    color,      (uvw, uvy)),
                ((x+s, s, y),  normal(0, 0, -1),    color,      (uvx, uvy)),
                ((x,   0, y),  normal(0, 0, -1),    color,      (uvw, uvh)),
                ((x+s, 0, y),  normal(0, 0, -1),    color,      (uvx, uvh))
            ], dtype=VERTEX_DTYPE),
            np.array([0, 1, 2, 2, 1, 3], dtype=np.uint32)
        )

    if not bottom_neighbour:
        mesh.add_geometry(
            np.array([
                ((x,   s, y-s),  normal(0, 0, 1),  color,    (uvx, uvy)),
                ((x+s, s, y-s),  normal(0, 0, 1),  color,    (uvw, uvy)),
                ((x,   0, y-s),  normal(0, 0, 1),  color,    (uvx, uvh)),
                ((x+s, 0, y-s),  normal(0, 0, 1),  color,    (uvw, uvh)),
            ], dtype=VERTEX_DTYPE),
            np.array([1, 0, 2, 1, 2, 3], dtype=np.uint32)
        )

    if not left_neighbour:
        mesh.add_geometry(
            np.array([
                ((x, s, y),       normal(1, 0, 0),  color,    (uvx, uvy)),
                ((x, s, y-s),     normal(1, 0, 0),  color,    (uvw, uvy)),
                ((x, 0, y),       normal(1, 0, 0),  color,    (uvx, uvh)),
                ((x, 0, y-s),     normal(1, 0, 0),  color,    (uvw, uvh)),
            ], dtype=VERTEX_DTYPE),
            np.array([1, 0, 2, 1, 2, 3], dtype=np.uint32)
        )

    if not right_neighbour:
        mesh.add_geometry(
            np.array([
                ((x+s, s, y),     normal(-1, 0, 0),  color,    (uvw, uvy)),
                ((x+s, s, y-s),   normal(-1, 0, 0),  color,    (uvx, uvy)),
                ((x+s, 0, y),     normal(-1, 0, 0),  color,    (uvw, uvh)),
                ((x+s, 0, y-s),   normal(-1, 0, 0),  color,    (uvx, uvh)),
            ], dtype=VERTEX_DTYPE),
            np.array([0, 1, 2, 2, 1, 3], dtype=np.uint32)
        )

    return mesh if not mesh.is_empty() else None 

def gen_platform_mesh(
    coords: tuple[int, int], 
    size: float, 
    y: float,
    color: tuple[int, int, int],
    uv_region: tuple[int, int, int, int],
    reverse: bool
) -> DynamicMeshCPU:
    s = size
    x, z = coords
    x, z = x*s, z*s

    indices = [0, 1, 2, 1, 3, 2] if reverse else [2, 1, 0, 1, 2, 3]
    normal_dir = 1 if reverse else -1

    uvx, uvy, uvw, uvh = uv_region
    uvw, uvh = uvx+uvw, uvy+uvh

    return DynamicMeshCPU(
        np.array([
            ((x,   y, z),    normal(0, normal_dir, 0),  color,    (uvx, uvy)),
            ((x+s, y, z),    normal(0, normal_dir, 0),  color,    (uvw, uvy)),
            ((x,   y, z-s),  normal(0, normal_dir, 0),  color,    (uvx, uvh)),
            ((x+s, y, z-s),  normal(0, normal_dir, 0),  color,    (uvw, uvh)),
        ], dtype=VERTEX_DTYPE),
        np.array(indices, dtype=np.uint32),
        vertex_dtype=VERTEX_DTYPE
    )

def gen_map_models(
    gfx: GraphicsContext, 
    assets: AssetManager, 
    model_renderer: ModelRenderer,
    worldmap: WorldMap,
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
    white_texture = gfx.get_white_texture()

    tilemap = worldmap.get_map()
    tiles = tilemap.get_tiles()

    color_map = worldmap.get_color_map()
    transparent_tiles = worldmap.get_transparent_tiles()

    # A mesh group is a dictionary, where keys are textures, and values are meshes
    mesh_group: dict[gl.Texture, DynamicMeshCPU] = {}

    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if tile != 0:
                neighbours = tilemap.get_neighbours((x, y))
                neighbours = tuple(has_neighbour(tile, n, transparent_tiles) if n else False for n in neighbours)

                # A material is either a color or a texture path
                material = color_map[tile]

                color = (255, 255, 255) if type(material) is str else material
                texture = assets.load(Texture, material) if type(material) is str else white_texture

                tile_mesh = gen_tile_mesh(
                    (x, -y), 
                    TILE_SIZE,
                    color,
                    texture.region,
                    neighbours
                )

                gl_texture = texture.texture
                if tile_mesh is not None:
                    if (group_mesh := mesh_group.get(gl_texture)):
                        group_mesh.add_mesh(tile_mesh)
                    else:
                        mesh_group[gl_texture] = tile_mesh
            
            if tile == 0 or (tile in transparent_tiles):
                floor_mesh = gen_platform_mesh(
                    (x, -y), 
                    TILE_SIZE, 
                    0, 
                    FLOOR_COLOR, 
                    white_texture.region,
                    False
                )

                # Generate the ceiling mesh
                floor_mesh.add_mesh(
                    gen_platform_mesh(
                        (x, -y), 
                        TILE_SIZE, 
                        TILE_SIZE, 
                        CEILING_COLOR, 
                        white_texture.region,
                        True
                    )
                )

                gl_texture = white_texture.texture
                if gl_texture in mesh_group:
                    mesh_group[gl_texture].add_mesh(floor_mesh)
                else:
                    mesh_group[gl_texture] = floor_mesh

    pipeline = model_renderer.get_pipeline()
    models = [
        (Model(ctx, group_mesh, pipeline, vertex_format=VERTEX_GL_FORMAT), group_texture) 
        for group_texture, group_mesh in mesh_group.items()
    ]
    return models
    
class MapModel:
    def __init__(
        self, 
        gfx: GraphicsContext, 
        assets: AssetManager, 
        renderer: ModelRenderer, 
        world_map: WorldMap
    ):
        self.models = gen_map_models(gfx, assets, renderer, world_map)

    def get_models(self) -> list[tuple[Model, gl.Texture]]:
        return self.models  

    def release(self):
        "Clear this map model from GPU"

        for model, _ in self.models:
            model.release()
        self.models.clear()

@run_if(resource_exists, MapModel)
def render_map(resources: Resources):
    map_model = resources[MapModel]
    renderer = resources[ModelRenderer]

    for model in map_model.get_models():
        renderer.push_model(*model)

def unload_map_model(resources: Resources):
    "A helper function that will perform map model clean up if present"

    if MapModel in resources:
        print("Releasing the old map")
        resources[MapModel].release()
        resources.remove(MapModel)

def load_map_model(resources: Resources, wmap: WorldMap):
    "A helper function that will load a new map model and clean up the old map model if present"

    unload_map_model(resources)

    resources.insert(MapModel(
        resources[GraphicsContext], 
        resources[AssetManager], 
        resources[ModelRenderer], 
        wmap
    ))

def on_worldmap_loaded(resources: Resources, _):
    "When a world map is loaded, we would like to generate a map model for it"

    load_map_model(resources, resources[WorldMap])

def on_worldmap_unloaded(resources: Resources, _):
    "If a world map is unloaded - we will clean up the map model"

    unload_map_model(resources)

class MapRendererPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.PostDraw, render_map)

        app.add_event_listener(WorldMapLoadedEvent, on_worldmap_loaded)
        app.add_event_listener(WorldMapUnloadedEvent, on_worldmap_unloaded)