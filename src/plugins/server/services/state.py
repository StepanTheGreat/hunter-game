from plugin import Plugin, Resources, EventWriter

from plugins.server.commands import StartGameCommand, FinishGameCommand
from plugins.server.events import GameFinishedEvent, GameStartedEvent

from enum import Enum, auto

class GameState(Enum):
    "The current state of the game. Even though it's an enum - it's actually also a resource"

    WaitingForPlayers = auto()
    InGame = auto()
    Finishing = auto()

def on_start_game_command(resources: Resources, _):
    ewriter = resources[EventWriter]
    
    assert resources[GameState] is GameState.WaitingForPlayers, "Can't start a game again"

    resources[GameState] = GameState.InGame
    ewriter.push_event(GameStartedEvent())

def on_finish_game_command(resources: Resources, _):
    ewriter = resources[EventWriter]
    
    assert resources[GameState] is GameState.InGame, "Can't finish a game that hasn't started or is already finished"
    
    resources[GameState] = GameState.Finishing
    ewriter.push_event(GameFinishedEvent())


class GameStatePlugin(Plugin):
    def build(self, app):
        app.insert_resource(GameState.WaitingForPlayers)

        app.add_event_listener(StartGameCommand, on_start_game_command)
        app.add_event_listener(FinishGameCommand, on_finish_game_command)