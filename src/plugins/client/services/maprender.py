"Map rendering"

import numpy as np
import moderngl as gl

from plugin import Resources, Plugin, Schedule, run_if, resource_exists

from typing import Optional

from plugins.shared.interfaces.map import *
from plugins.client.events import WorldMapLoadedEvent, WorldMapUnloadedEvent

from plugins.client.services.graphics.render3d import * 

from core.graphics import *
from core.assets import AssetManager

# Just a default white color
WHITE_COLOR = (255, 255, 255)

IGNORE_TILES = (0, PLAYER_SPAWNPOINT, ROBBER_SPAWNPOINT, DIAMOND_SPAWNPOINT)

def _bitcrush(x: float) -> float:
    return max(min(x * 128, 127), -128)

def normal(x: float, y: float, z: float):
    "Bit crush this normal's coordinates into byte range between -128 and 127"
    return _bitcrush(x), _bitcrush(y), _bitcrush(z)

def gen_tile_mesh(
    coords: tuple[int, int], 
    width: float,
    height: float, 
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
    w, h = width, height
    x, y = coords
    x, y = x*w, y*w
    top_neighbour, left_neighbour, right_neighbour, bottom_neighbour = neighbours

    uvx, uvy, uvw, uvh = uv_region
    uvw, uvh = uvx+uvw, uvy+uvh

    mesh = DynamicMeshCPU(
        np.array([], dtype=MODEL_VERTEX_DTYPE),
        np.array([], dtype=np.uint32),
        vertex_dtype=MODEL_VERTEX_DTYPE
    )

    if not top_neighbour:
        mesh.add_geometry(
            np.array([
                ((x,   h, y),  normal(0, 0, -1),    color,      (uvw, uvy)),
                ((x+w, h, y),  normal(0, 0, -1),    color,      (uvx, uvy)),
                ((x,   0, y),  normal(0, 0, -1),    color,      (uvw, uvh)),
                ((x+w, 0, y),  normal(0, 0, -1),    color,      (uvx, uvh))
            ], dtype=MODEL_VERTEX_DTYPE),
            np.array([0, 1, 2, 2, 1, 3], dtype=np.uint32)
        )

    if not bottom_neighbour:
        mesh.add_geometry(
            np.array([
                ((x,   h, y-w),  normal(0, 0, 1),  color,    (uvx, uvy)),
                ((x+w, h, y-w),  normal(0, 0, 1),  color,    (uvw, uvy)),
                ((x,   0, y-w),  normal(0, 0, 1),  color,    (uvx, uvh)),
                ((x+w, 0, y-w),  normal(0, 0, 1),  color,    (uvw, uvh)),
            ], dtype=MODEL_VERTEX_DTYPE),
            np.array([1, 0, 2, 1, 2, 3], dtype=np.uint32)
        )

    if not left_neighbour:
        mesh.add_geometry(
            np.array([
                ((x, h, y),       normal(1, 0, 0),  color,    (uvx, uvy)),
                ((x, h, y-w),     normal(1, 0, 0),  color,    (uvw, uvy)),
                ((x, 0, y),       normal(1, 0, 0),  color,    (uvx, uvh)),
                ((x, 0, y-w),     normal(1, 0, 0),  color,    (uvw, uvh)),
            ], dtype=MODEL_VERTEX_DTYPE),
            np.array([1, 0, 2, 1, 2, 3], dtype=np.uint32)
        )

    if not right_neighbour:
        mesh.add_geometry(
            np.array([
                ((x+w, h, y),     normal(-1, 0, 0),  color,    (uvw, uvy)),
                ((x+w, h, y-w),   normal(-1, 0, 0),  color,    (uvx, uvy)),
                ((x+w, 0, y),     normal(-1, 0, 0),  color,    (uvw, uvh)),
                ((x+w, 0, y-w),   normal(-1, 0, 0),  color,    (uvx, uvh)),
            ], dtype=MODEL_VERTEX_DTYPE),
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
        ], dtype=MODEL_VERTEX_DTYPE),
        np.array(indices, dtype=np.uint32),
        vertex_dtype=MODEL_VERTEX_DTYPE
    )

def gen_map_models(
    gfx: GraphicsContext, 
    assets: AssetManager, 
    model_renderer: ModelRenderer,
    worldmap: WorldMap,
) -> list[tuple[Model, gl.Texture]]:
    "Generate an array of renderable map models"

    def has_neighbour(wall: int, nwall: int, opaque_walls: set[int]) -> bool:
        # This is a simple culling neighbour culling function.
        # Basically, we would like to check if a wall has a neighbour.
        #
        # If a wall is normal and it has a non-opaque neighbour - it does have a neighbour.
        # If a wall is normal and it has an opaque neighbour - it "doesn't"
        # If a wall is opaque and its neighbour isn't - it does have a neighbour 

        return (nwall in IGNORE_TILES) or (wall in opaque_walls) or (nwall not in opaque_walls)
    
    ctx = gfx.get_context()

    wall_width, wall_height = worldmap.get_wall_size() 

    ceiling_map = worldmap.get_ceiling_map()
    floor_map = worldmap.get_floor_map()
    wall_map = worldmap.get_wall_map()

    walls = wall_map.get_tiles()
    opaque_walls = worldmap.get_opaque_walls()

    # A mesh group is a dictionary, where keys are textures, and values are meshes
    mesh_group: dict[gl.Texture, DynamicMeshCPU] = {}

    for y, row in enumerate(walls):
        for x, tile in enumerate(row):
            if tile not in IGNORE_TILES:
                neighbours = wall_map.get_neighbours((x, y))

                neighbours = tuple(neighbour and has_neighbour(tile, neighbour, opaque_walls) for neighbour in neighbours)

                if not all(neighbours): 
                    # If there's at least one absent neighbour (where our tile's face can be seen) - 
                    # we're going to generate the mesh. In any other case we shouldn't even bother

                    wall_prop = worldmap.get_wall_prop(tile)
                    texture = assets.load(Texture, wall_prop.texture)

                    tile_mesh = gen_tile_mesh(
                        (x, -y), 
                        wall_width,
                        wall_height,
                        WHITE_COLOR,
                        texture.region,
                        neighbours
                    )

                    gl_texture = texture.texture
                    if (group_mesh := mesh_group.get(gl_texture)):
                        group_mesh.add_mesh(tile_mesh)
                    else:
                        mesh_group[gl_texture] = tile_mesh
            
            if tile in IGNORE_TILES or (tile in opaque_walls):
                
                floor_tile = floor_map.get_tile(x, y)

                if floor_tile != 0:
                    floor_texture = assets.load(
                        Texture,
                        worldmap.get_platform_texture(floor_tile)
                    )

                    floor_mesh = gen_platform_mesh(
                        (x, -y), 
                        wall_width, 
                        0, 
                        WHITE_COLOR, 
                        floor_texture.region,
                        False
                    )

                    gl_floor_texture = floor_texture.texture
                    if gl_floor_texture in mesh_group:
                        mesh_group[gl_floor_texture].add_mesh(floor_mesh)
                    else:
                        mesh_group[gl_floor_texture] = floor_mesh

                ceiling_tile = ceiling_map.get_tile(x, y)

                if ceiling_tile != 0:
                
                    ceiling_texture = assets.load(
                        Texture,
                        worldmap.get_platform_texture(ceiling_tile)
                    )

                    ceiling_mesh = gen_platform_mesh(
                        (x, -y), 
                        wall_width, 
                        wall_height, 
                        WHITE_COLOR, 
                        ceiling_texture.region,
                        True
                    )

                    gl_ceiling_texture = ceiling_texture.texture
                    if gl_ceiling_texture in mesh_group:
                        mesh_group[gl_ceiling_texture].add_mesh(ceiling_mesh)
                    else:
                        mesh_group[gl_ceiling_texture] = ceiling_mesh

    pipeline = model_renderer.get_pipeline()
    models = [
        (Model(ctx, group_mesh, pipeline, vertex_format=MODEL_VERTEX_GL_FORMAT), group_texture) 
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
        self.skybox_texture = assets.load(Texture, "images/skybox.png")

        self.skybox = SkyBox(*((self.skybox_texture, )*4))
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

    renderer.set_skybox(map_model.skybox)
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