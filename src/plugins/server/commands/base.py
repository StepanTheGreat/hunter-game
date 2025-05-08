from plugin import event

@event
class StopServerBroadcastingCommand:
    "A command that's issued whenever the server would like to stop issuing broadcasts"

@event
class StartGameCommand:
    "A command that switches the current game state to `InGame`"

@event
class FinishGameCommand:
    "A command that gets fired when the game is finished (i.e. when either the robber lose or the policemen)"