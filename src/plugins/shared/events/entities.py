from plugin import event

@event
class DiamondPickedUpEvent:
    "A diamond was picked up!"
    def __init__(self, ent: int):
        self.ent = ent

@event
class ProjectileHitEvent:
    "Fired whenever a projectile hits a hittable entity of an opposite team"

    def __init__(self, target_ent: int, damage: float):
        self.target_ent = target_ent
        self.damage = damage