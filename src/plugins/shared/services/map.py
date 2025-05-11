import numpy as np

from plugin import Plugin, Resources, EventWriter

from core.ecs import WorldECS
from core.assets import add_loaders

from file import load_file_str

from plugins.shared.events.map import *
from plugins.shared.commands.map import LoadMapCommand, UnloadMapCommand

from modules.tilemap import Tilemap
from plugins.shared.interfaces.map import WorldMap, WORLDMAP_JSON_SCHEMA, MapCamera, WallPropery, MapSkybox

from jsonschema import validate, ValidationError
from json import loads as json_loads

def loader_world_map(resources: Resources, path: str) -> WorldMap:
    "A custom loader for world maps. Extremely useful for both the server and the client"

    # This one is a bit heavy to parse, so I'll try to explain everything

    # First of course load our file as a string, then parse it as JSON
    map_str = load_file_str(path)
    map_json = json_loads(map_str)

    # We're going to validate it against our worldmap schema, and if it doesn't pass - we'll raise an exception
    try:
        validate(map_json, WORLDMAP_JSON_SCHEMA)
    except ValidationError as err:
        print(f"Failed to parse the map at {path}")
        raise err

    # Get our map size
    map_size = map_json["size"]

    # Tile width and height
    wall_width, wall_height = map_json["wall_width"], map_json["wall_height"]

    # We have 3 tilemaps, so we're loading these as well
    wall_map = Tilemap(map_size, map_size, np.array(map_json["wall_map"], dtype=np.uint32))
    floor_map = Tilemap(map_size, map_size, np.array(map_json["floor_map"], dtype=np.uint32))
    ceiling_map = Tilemap(map_size, map_size, np.array(map_json["ceiling_map"], dtype=np.uint32))

    # Because JSON only supports string keys, we're converting them here into integers.
    # Additionally, we're converting property entries here into `WallProperty` objects. `opaque`
    # attribute is optional, so by default it will be False
    wall_props: dict[int, WallPropery] = {
        int(k): WallPropery(props["texture"], props.get("opaque", False)) 
        for k, props in map_json["wall_props"].items()
    }

    # The same idea here, but platforms only get to set their texture as property
    platform_props: dict[int, str] = {
        int(k): v for k, v in map_json["platform_props"].items()
    }

    # Finally, construct the `MapCamera` object from the given data
    map_camera = map_json["map_camera"]
    map_camera = MapCamera((map_camera["x"], map_camera["y"]), map_camera["height"], map_camera["angle"])

    map_skybox = map_json.get("map_skybox")
    if map_skybox is not None:
        map_skybox = MapSkybox(map_skybox["left"], map_skybox["front"], map_skybox["right"], map_skybox["back"])

    # And return our world map object!
    return WorldMap(
        wall_map,
        floor_map,
        ceiling_map,
        wall_width,
        wall_height,
        wall_props,
        platform_props,
        map_camera,
        map_skybox
    )


def _load_world_map(resources: Resources, wmap: WorldMap):
    """
    Load a new world map, and if a map is already present - clean it up and overwrite with the new one.
    This function will automatically create map colliders and push appropriate events.
    """

    _unload_world_map(resources)

    # First we're going to insert all map's colliders
    wmap.create_map_entities(resources[WorldECS])

    resources.insert(wmap)

    resources[EventWriter].push_event(WorldMapLoadedEvent())

def _unload_world_map(resources: Resources):
    """
    Unload the current world map if present. This will automatically remove its 
    colliders and push appropriate events.
    """

    if WorldMap in resources:
        wmap = resources.remove(WorldMap)
        wmap.destroy_map_entities(resources[WorldECS])

        resources[EventWriter].push_event(WorldMapUnloadedEvent())

def on_load_map_command(resources: Resources, new_map: LoadMapCommand):
    _load_world_map(resources, new_map.map)

def on_unload_map_command(resources: Resources, _):
    _unload_world_map(resources)

class WorldMapPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(LoadMapCommand, on_load_map_command)
        app.add_event_listener(UnloadMapCommand, on_unload_map_command)

        add_loaders(app, (WorldMap, loader_world_map))