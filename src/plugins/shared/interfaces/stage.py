from enum import Enum

class GameNotification(Enum):
    "A shared message enum that's sent by the server to signal some specific event"

    GameStarted = 0
    "The game just started"

    LightsOn = 1
    "Lights are one, the robber has either lost his first diamond, or was found by a policeman"

    PolicemenWon = 2
    "The policemen have won the game"

    RobberWon = 3
    "The robber has won the game"