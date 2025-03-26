from enum import Enum, auto
from typing import Union

from plugin import EventWriter, event

class SceneState(Enum):
    "A simple enum class that describes different ingame states"
    MainMenu = auto(),
    InGame = auto()

class AppState:
    "Simply a global resource for checking app's state"
    def __init__(self, ewriter: EventWriter, state: SceneState):
        self.event_writer = ewriter
        self.state = state

    def __eq__(self, other: Union[SceneState, "AppState"]) -> bool:
        if type(other) == SceneState:
            return self.state == other
        elif type(other) == AppState:
            return self.state == other.state
        
        assert False, "Can only compare against AppState and SceneState" 

    def set_state(self, to: SceneState):
        "Change this scene to a new one and fire a state-switch event"
        self.event_writer.push_event(StateSwitchEvent(self.state, to))
        self.state = to

@event
class StateSwitchEvent:
    "An event that gets fired whenever a state switch has happened. All attributes of this object are public"
    def __init__(self, old: SceneState, new: SceneState):
        self.old = old
        self.new = new