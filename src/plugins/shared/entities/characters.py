from core.ecs import WorldECS

from plugins.shared.components import *

ROBBER_HEALTH = 2500
ROBBER_SPEED = 230

ROBBER_PROJECTILE = ProjectileFactory(
    True,
    speed=10,
    radius=20,
    damage=50,
    lifetime=0.1,
    spawn_offset=15,
)

ROBBER_WEAPON_STATS = WeaponStats(0.2, True)

POLICEMAN_HEALTH = 500
POLICEMAN_SPEED = 200

POLICEMAN_PROJECTILE = ProjectileFactory(
    False,
    speed=700,
    radius=5,
    damage=100,
    lifetime=1,
    spawn_offset=0,
)

POLICEMAN_WEAPON_STATS = WeaponStats(0.4, True)
    
def make_policeman(uid: int, pos: tuple[float, float]) -> tuple:
    components = (
        Position(*pos),
        Velocity(0, 0, POLICEMAN_SPEED),
        AngleVelocity(0, 4),
        Angle(0),
        DynCollider(12, 30),
        Weapon(POLICEMAN_PROJECTILE, POLICEMAN_WEAPON_STATS),
        PlayerController(),
        Team.friend(),
        Hittable(),
        Health(POLICEMAN_HEALTH, 0.25),
        NetEntity(uid),
        NetSyncronized(),
        Policeman(),
        Player(),
    )
    
    return components

def crookify_policeman(world: WorldECS, ent: int):
    "A helper function for transforming an existing policeman entity into a robber"

    assert world.contains_entity(ent)

    # First we're going to remove most of the key components from it
    world.remove_components(
        ent, 
        Health, 
        Velocity,
        DynCollider, 
        Weapon, 
        Team,
        Policeman
    )

    # And then simply reinsert them
    world.add_components(
        ent,
        Health(ROBBER_HEALTH, 0.25),
        Velocity(0, 0, ROBBER_SPEED), # The robber is going to be a bit faster
        DynCollider(18, 30),
        Weapon(ROBBER_PROJECTILE, ROBBER_WEAPON_STATS),
        Team.enemy(),
        Robber()
    )