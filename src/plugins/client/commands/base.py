from plugin import event

@event
class ResetPlayerStatsHealthCommand:
    "A command that tells the player stats service to reset player's health"

@event
class UpdatePlayerStatsHealthCommand:
    "A command that tells the player stats to update the current player's health to the provided value"

    def __init__(self, value: float):
        assert 0 <= value <= 1

        self.value = value

@event 
class CleanUpEntitiesCommand:
    "A command that tells to remove all game-related entities from the ECS world"

@event
class GameStartedCommand:
    "The game has started, even though in the darkness"

@event
class ResetSceneLightsCommand:
    "A command that resets the current client's lighting level to default (full)"