from plugin import Plugin, Resources, EventWriter

from core.ecs import WorldECS

from plugins.shared.events.map import *
from plugins.shared.commands.map import LoadMapCommand, UnloadMapCommand

from plugins.shared.interfaces.map import WorldMap

def _load_world_map(resources: Resources, wmap: WorldMap):
    """
    Load a new world map, and if a map is already present - clean it up and overwrite with the new one.
    This function will automatically create map colliders and push appropriate events.
    """

    _unload_world_map(resources)

    # First we're going to insert all map's colliders
    wmap.create_map_colliders(resources[WorldECS])

    resources.insert(wmap)

    resources[EventWriter].push_event(WorldMapLoadedEvent())

def _unload_world_map(resources: Resources):
    """
    Unload the current world map if present. This will automatically remove its 
    colliders and push appropriate events.
    """

    if WorldMap in resources:
        wmap = resources[WorldMap]
        wmap.destroy_map_colliders(resources[WorldECS])

        resources[EventWriter].push_event(WorldMapUnloadedEvent())

def on_load_map_command(resources: Resources, new_map: LoadMapCommand):
    _load_world_map(resources, new_map.map)

def on_unload_map_command(resources: Resources, _):
    _unload_world_map(resources)

class WorldMapPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(LoadMapCommand, on_load_map_command)
        app.add_event_listener(UnloadMapCommand, on_unload_map_command)