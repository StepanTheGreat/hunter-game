from plugin import event

@event
class GameStartedEvent:
    """
    Gets fired when the game has actually started. At that point the map should be loaded, players
    notified and so on.
    """