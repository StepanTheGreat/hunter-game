from core.ecs import component

@component
class Policeman:
    "The policeman tag"


@component
class Robber:
    "A robber tag"

@component
class Diamond:
    "A diamond entity tag. Diamonds are picked up by thieves to win the game"



@component
class PickingUp:
    NEEDS_TIME: float = 5

    def __init__(self):
        self.is_picking_up: bool = False
        self.picked_up = PickingUp.NEEDS_TIME

        self.got_picked_up: bool = False

    def tick(self, dt: float):
        "Tick the picking up component"

        if self.got_picked_up:
            return
        
        if self.is_picking_up:
            # If the item is getting picked up, we would like to reduce its lifetime
            self.picked_up -= dt

            # And if 0 - set is as already picked up
            if self.picked_up < 0:
                self.got_picked_up = True
        elif self.picked_up < PickingUp.NEEDS_TIME:
            # If however it's not, we would like to fill its time back
            self.picked_up += dt

    def set_picking_up(self, to: bool):
        "Set this to picking up, thus every tick the item will update"

        self.is_picking_up = to

    def is_picked_up(self) -> bool:
        "Was this item picked up?"

        return self.got_picked_up