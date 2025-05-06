from core.ecs import component

@component
class PlayerAddress:
    """
    The player's bound socket address. Highly useful for ECS to be able to communicate who is who,
    without reaching the global state
    """
    def __init__(self, addr: tuple[str, int]):
        self.addr = addr

    def get_addr(self) -> tuple[str, int]:
        return self.addr