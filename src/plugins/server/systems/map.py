from plugin import Plugin, Resources, Schedule, EventWriter

from core.assets import AssetManager

from plugins.shared.commands import LoadMapCommand
from plugins.shared.interfaces.map import WorldMap

from plugins.server.components import *
from plugins.server.actions import *

def load_map_on_startup(resources: Resources):
    "On startup, we simply would like to load our game map"

    assets = resources[AssetManager]
    ewriter = resources[EventWriter]

    world_map = assets.load(WorldMap, "maps/map1.json")
    ewriter.push_event(LoadMapCommand(world_map))

class MapSystemsPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Startup, load_map_on_startup)