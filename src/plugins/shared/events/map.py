from plugin import event

@event
class WorldMapLoadedEvent:
    "Fired when a world map gets loaded"

@event
class WorldMapUnloadedEvent:
    "Fired whenever a world map get unloaded"