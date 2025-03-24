"Sorry, no, I'm not going to make a physics engine in python"

from enum import Enum

import pymunk as pm
import pygame as pg

class ColliderType:
    Static = pm.Body.STATIC
    "Static bodies are bodies that never (or rarely) move."

    Dynamic = pm.Body.DYNAMIC
    """
    They react to collisions, are affected by forces and gravity, and have a finite amount of mass. 
    These are the type of bodies that you want the physics engine to simulate for you. 
    Dynamic bodies interact with all types of bodies and can generate collision callbacks.
    """

    Kinematic = pm.Body.KINEMATIC
    """
    They arent affected by gravity and they have an infinite amount of mass so they don't react to collisions or forces with other bodies. 
    Kinematic bodies are controlled by setting their velocity, which will cause them to move. 
    Good examples of kinematic bodies might include things like moving platforms. 
    Objects that are touching or jointed to a kinematic body are never allowed to fall asleep.
    """


class Collider:
    "A simplified abstraction for a physics body and shape. Don't create this object yourself - use constructor functions instead"
    def __init__(self, shape: pm.Shape, body: pm.Body):
        self.body = body
        self.shape = shape

    def with_position(self, to: pg.Vector2):
        "Just a constructor method"
        self.set_position(to)
        return self

    def set_position(self, to: pg.Vector2):
        self.body.position = (to.x, to.y)

    def set_velocity(self, to: pg.Vector2):
        self.body.velocity = (to.x, to.y)

    def get_position(self) -> pg.Vector2:
        return pg.Vector2(*self.body.position)
    
def make_ball_collider(radius: float, position: tuple, body_type: ColliderType, mass: float = 1) -> Collider:
    "Construct a ball collider"

    assert mass > 0, "Mass can't be negative or zero"

    body = pm.Body(mass=mass, body_type=body_type)
    shape = pm.Circle(body, radius)
    shape.mass = mass
    body.position = position

    return Collider(shape, body)

def make_rect_collider(position: tuple, size: tuple, body_type: ColliderType, mass: float = 1) -> Collider:
    "Construct a rect collider"

    assert mass > 0, "Mass can't be negative or zero"

    x, y = position 
    w, h = size

    body = pm.Body(mass=mass, body_type=body_type)
    shape = pm.Poly(body, vertices=[
        (-w/2,     -h/2),
        (w/2,   -h/2),
        (-w/2,     h/2),
        (w/2,   h/2)
    ])
    shape.mass = mass
    body.position = (x+w/2, y+h/2)

    return Collider(shape, body)

class PhysicsWorld:
    def __init__(self, gravity: tuple):
        self.space = pm.Space()
        self.space.gravity = gravity

    def add_collider(self, collider: Collider):
        self.space.add(collider.body, collider.shape)
    
    def remove_collider(self, collider: Collider):
        self.space.remove(collider.body, collider.shape)

    def step(self, dt: float):
        "Step this simulation by a provided delta time. Make sure to use constant values to achieve smoother simulation"
        self.space.step(dt)