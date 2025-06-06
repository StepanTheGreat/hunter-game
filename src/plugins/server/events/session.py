from plugin import event

@event
class GameStartedEvent:
    """
    Gets fired when the game has actually started. At that point the map should be loaded, players
    notified and so on.
    """

@event
class LightsOnEvent:
    "An event that simply means that the game has entered the second sub-faze, thus turning on the lights"

@event
class GameFinishedEvent:
    "Fired when the game has ended and there's nothing to do. Used for cleanup"

@event
class AddedClientEvent:
    "A new client was registered into the entity world"

    def __init__(self, addr: tuple[str, int], ent: int):
        self.addr = addr
        self.ent = ent

@event
class RemovedClientEvent:
    "A client was removed from the world (due to disconnection)"

    def __init__(self, addr: tuple[str, int], ent: int):
        self.addr = addr
        self.ent = ent