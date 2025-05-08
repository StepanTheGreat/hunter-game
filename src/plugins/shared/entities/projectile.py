from plugins.shared.components import *

def make_projectile(
    factory: ProjectileFactory,
    pos: tuple[float, float], 
    direction: tuple[float, float], 
) -> tuple:
    return factory.make_projectile(pos, direction)