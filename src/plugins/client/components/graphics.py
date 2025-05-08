import pygame as pg

from core.ecs import component

from core.graphics import Texture

@component
class Light:
    def __init__(self, y: float, color: tuple[float, float, float], radius: float, luminosity: float):
        assert luminosity > 0
        assert radius > 0

        self.color = color
        self.radius = radius
        self.luminosity = luminosity
        self.y = y

@component
class Sprite:
    "A sprite component that allows an entity to be rendered as 2D billboards"
    def __init__(self, y: float, texture: Texture, size: tuple[int, int]):
        self.y: float = y
        self.texture: Texture = texture
        self.size: pg.Vector2 = pg.Vector2(size[0], size[1])