from plugins.shared.events import *

@event
class CharacterUsedWeaponEvent:
    "Gets fired whenever one of the characters (either a policeman or the robber) use their weapons"

    def __init__(self, is_policeman: bool, is_main: bool):
        self.is_policeman = is_policeman
        self.is_main = is_main

@event
class MainPlayerIsACrookEvent:
    "Fired whenever the unexpected happens... the main player... is a crook..."

@event
class MainPlayerDiedEvent:
    "The main player (the client THIS game is playing) has died"