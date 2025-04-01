import pygame as pg
from typing import Optional

from plugin import Resources, Plugin, Schedule, run_if, resource_exists

from core.pg import MouseMotionEvent, Screen
from core.graphics import FontGPU

from plugins.graphics import Renderer2D

class GUIContext:
    def __init__(self, width: int, height: int, renderer: Renderer2D):
        self.renderer = renderer
        self.width = width
        self.height = height

        self.x = 0
        self.y = 0

        self.same_line = None

    def reset(self):
        self.x = 0
        self.y = 0

    def on_same_line(self):
        self.same_line = True
    
    def label(self, font: FontGPU, text: str, color: tuple[float, ...], size: float = 1):
        textw, texth = font.measure(text)
        self.renderer.draw_text(font, text, (self.x, self.y), color, size)

        if self.same_line:
            self.x += textw
        else:
            self.y += texth

def reset_gui(resources: Resources):
    resources[GUIContext].reset()

class GUIManagerPlugin(Plugin):
    def build(self, app):
        screen = app.get_resource(Screen)
        app.insert_resource(GUIContext(*screen.get_size(), app.get_resource(Renderer2D)))
        app.add_systems(Schedule.PreUpdate, reset_gui)