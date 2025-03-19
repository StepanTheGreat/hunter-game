from plugin import *
from modules.tilemap import Tilemap

import numpy as np

class WorldMap:
    "The globally explorable, renderable map"
    def __init__(self, tilemap: Tilemap):
        self.map = tilemap

class MapPlugin(Plugin):
    def build(self, app):
        app.insert_resource(WorldMap(
            Tilemap(8, 8, np.array([
                [0, 0, 0, 0, 0, 0, 2, 2],
                [2, 1, 1, 0, 0, 0, 0, 2],
                [3, 0, 0, 2, 0, 0, 0, 1],
                [1, 0, 0, 4, 1, 1, 0, 1],
                [3, 0, 0, 0, 0, 0, 0, 2],
                [2, 0, 0, 0, 0, 0, 0, 2],
                [2, 0, 0, 0, 0, 0, 0, 3],
                [1, 3, 0, 0, 0, 0, 3, 3],
            ], dtype=np.uint32))
        ))

def render_map(resources: Resources):
    pass
        

