from plugins.collisions import DynCollider

from plugins.graphics import Sprite

class ColliderComponent:
    "A collider component which basically stores a reference to its internal collider"
    def __init__(self, collider: DynCollider):
        self.collider = collider

class PositionComponent:
    "An entity position. If added with Collider component - it will also get automatically overwritten by Collider's interpolated position"
    def __init__(self, x: float, y: float, height: float):
        self.x = x
        self.y = y
        self.height = height

    def as_renderable(self) -> tuple[float, float, float]:
        "In rendering, the Y coordinate (or in 3D Z) is reversed"
        return (self.x, self.height, -self.y)
    
class SpriteComponent:
    def __init__(self, sprite: Sprite):
        self.sprite = sprite

class HealthComponent:
    def __init__(self, max_health: float):
        self.health = max_health
        self.max_health = max_health

    def hurt(self, by: int):
        assert by >= 0, "Can't deal negative damage"

        self.health = max(self.health-by, 0)

    def heal(self, by: int):
        assert by >= 0, "Can't heal by a negative amount"

        self.health = min(self.health+by, self.max_health)

    def get_health(self) -> float:
        return self.health

    def get_percentage(self) -> float:
        "Return the fraction of health to the max health. This can be useful for rendering health bars"
        return self.health/self.max_health
    
class Timer:
    "A general purpose timer, be it for cooldowns or any other stuff"
    def __init__(self, duration: float, current_duration: float = 0):
        self.duration = duration
        self.current_duration = current_duration

    def update(self, dt: float):
        if self.current_duration > 0:
            self.current_duration -= dt

    def has_finished(self) -> bool:
        return self.current_duration <= 0

    def reset(self):
        "Reset this timer back to its duration"
        self.current_duration = self.duration
