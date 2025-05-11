from plugin import event
from enum import Enum, auto

class CheckoutScene(Enum):
    "Which scene to checkout?"
    
    MainMenu = auto()
    InGame = auto()

@event
class CheckoutSceneCommand:
    "A command that allows switching the current scene to a new one"

    def __init__(self, new_scene: CheckoutScene):
        self.new_scene = new_scene