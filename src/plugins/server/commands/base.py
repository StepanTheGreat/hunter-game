from plugin import event

@event
class StopServerBroadcastingCommand:
    "A command that's issued whenever the server would like to stop issuing broadcasts"