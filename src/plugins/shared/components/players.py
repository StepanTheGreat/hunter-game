from core.ecs import component

@component
class Player:
    "A tag component that allows filtering out players"

@component
class MainPlayer:
    "A tag that allows distinguishing the current client from other clients"

@component
class PlayerController:
    """
    The state of the current player's input. This is used by 
    """
    def __init__(self):
        self.forward_dir = 0
        self.horizontal_dir = 0
        self.is_shooting = False