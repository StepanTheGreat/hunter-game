from plugin import event

@event
class CrookifyRandomPlayerCommand:
    """
    A procedure that essentially is going to take a random player, give it robber components,
    and also dispatch appropriate action to notify all other players.
    """