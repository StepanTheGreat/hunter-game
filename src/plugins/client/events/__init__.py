from plugins.shared.events import *

@event
class CharacterUsedWeaponEvent:
    "Gets fired whenever one of the characters (either a policeman or the robber) use their weapons"

    def __init__(self, is_policeman: bool, is_main: bool):
        self.is_policeman = is_policeman
        self.is_main = is_main