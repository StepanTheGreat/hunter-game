from plugin import event

from plugins.shared.interfaces.map import WorldMap

@event
class LoadMapCommand:
    "A command to load the provided map and overwrite the previous one"
    def __init__(self, map: WorldMap):
        self.map = map

@event
class UnloadMapCommand:
    "A command to unload the currently loaded world map (if present)"