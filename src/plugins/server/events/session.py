from plugin import event

@event
class GameStartedEvent:
    """
    Gets fired when the game has actually started. At that point the map should be loaded, players
    notified and so on.
    """

@event
class GameFinishedEvent:
    "Fired when the game has ended and there's nothing to do. Used for cleanup"

@event
class AddedClient:
    "A new client was registered into the entity world"

    def __init__(self, addr: tuple[str, int], ent: int):
        self.addr = addr
        self.ent = ent

@event
class RemovedClient:
    "A client was removed from the world (due to disconnection)"

    def __init__(self, addr: tuple[str, int], ent: int):
        self.addr = addr
        self.ent = ent