from plugin import Plugin, Resources, EventWriter

from plugins.server.commands import StartGameCommand, FinishGameCommand
from plugins.server.events import GameFinishedEvent, GameStartedEvent

from enum import Enum, auto

class GameState(Enum):
    "Different states of the game"

    WaitingForPlayers = auto()
    InGame = auto()
    Finishing = auto()

class CurrentGameState:
    "A resource that stores the current state of the game. Can be directly compared with `GameState`"
    def __init__(self, default: GameState):
        self.state = default

    def __eq__(self, state: GameState) -> bool:
        return self.state == state
    
    def get_state(self) -> GameState:
        return self.state
    
    def _set_state(self, new_state: GameState):
        self.state = new_state

def on_start_game_command(resources: Resources, _):
    ewriter = resources[EventWriter]
    state = resources[CurrentGameState]

    assert state == GameState.WaitingForPlayers, "Can't start a game again"

    state._set_state(GameState.InGame)
    ewriter.push_event(GameStartedEvent())

def on_finish_game_command(resources: Resources, _):
    ewriter = resources[EventWriter]
    state = resources[CurrentGameState]
    

    assert state == GameState.InGame, "Can't finish a game that hasn't started or is already finished"
    
    state._set_state(GameState.Finishing)
    ewriter.push_event(GameFinishedEvent())

class GameStatePlugin(Plugin):
    def build(self, app):
        app.insert_resource(CurrentGameState(GameState.WaitingForPlayers))

        app.add_event_listener(StartGameCommand, on_start_game_command)
        app.add_event_listener(FinishGameCommand, on_finish_game_command)