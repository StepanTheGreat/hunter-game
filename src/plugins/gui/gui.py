import pygame as pg
from typing import Optional, Callable

from enum import Enum, auto

from plugin import Resources, Plugin, Schedule

from core.pg import MouseMotionEvent, Screen, WindowResizeEvent
from core.input import InputManager, MouseButton
from core.graphics import FontGPU
from core.assets import AssetManager

from plugins.graphics.render2d import Renderer2D

class GUIElement:
    """
    The purpose of using GUI elements is to centralize all update and rendering logic into one
    """
    def __init__(self, id: str, position: tuple[float, float], size: tuple[float, float], pivot: tuple[float, float]):
        self.id: str = id

        self.resolution_ptr: pg.Vector2 = None
        # This is a highly ugly approach, but we need some way to pass a shared resolution object to 
        # our objects, so that they can resize whenever they need 

        self.size = size
        self.position = position
        self.draw_rect = None
        self.pivot = pivot

    def bind_resolution_ptr(self, resolution: pg.Vector2):
        self.resolution_ptr = resolution
        
    def compute_rect(self, width: int, height: int) -> pg.Rect:
        "Compute this element's position accross the entire . Highly useful to avoid manual positioning"
        return pg.Rect(
            (self.position[0] - self.pivot[0] * self.size[0])*width,
            (self.position[1] - self.pivot[1] * self.size[1])*height,
            self.size*width,
            self.size*height
        )
    
    def get_rect(self) -> pg.Rect:
        return self.draw_rect.copy()

    def resize(self):
        "Element's custom resizing"
        w, h = self.resolution_ptr.x, self.resolution_ptr.y
        self.draw_rect = self.compute_rect(w, h)

    def get_id(self) -> str:
        return self.id
        
    def update(self, resources: Resources, input: InputManager):
        "Element's update logic whenever input is present"

    def draw(self, resources: Resources, renderer: Renderer2D):
        "Element's draw logic"

class Label(GUIElement):
    def __init__(
            self, 
            id: int, 
            font: FontGPU, 
            text: str, 
            position: tuple[float, float],
            pivot: tuple[float, float] = (0, 0),
            scale: float = 1
        ):
        self.font = font
        self.text = text
        self.text_scale = scale

        super().__init__(id, position, (0, 0), pivot)

    def compute_rect(self, width: int, height: int) -> pg.Rect:
        textw, texth = self.font.measure(self.text)
        textw, texth = textw*self.text_scale, texth*self.text_scale

        return pg.Rect(
            self.position[0]*width - self.pivot[0]*textw,
            self.position[1]*height - self.pivot[1]*texth,
            textw,
            texth
        )
    
    def set_text(self, text: str):
        "Changing the text will recompute its rectangle"
        self.text = text
        self.resize()

    def draw(self, _, renderer):
        renderer.draw_text(self.font, self.text, self.draw_rect.topleft, (1, 1, 1), self.text_scale)

class Button(Label):
    def __init__(
            self, 
            id, 
            font, 
            text, 
            position, 
            pivot = (0, 0), 
            text_scale = 1,
            button_color: tuple[float, ...] = (0.2, 0.2, 0.2),
            clicked_color: tuple[float, ...] = (0.1, 0.1, 0.1)
        ):
        super().__init__(id, font, text, position, pivot, text_scale)
        self.button_color = button_color
        self.clicked_color = clicked_color
        self.clicked = True

    def update(self, _, input: InputManager):
        pressed = input.is_mouse_down(MouseButton.Left)

        if not self.clicked and pressed:
            x, y, w, h = self.draw_rect
            mx, my = input.get_mouse_pos()

            if x <= mx <= x+w and y <= my <= y+h:
                self.clicked = True
                print("Clicked on the button!")
        elif self.clicked and not pressed:
            self.clicked = False

    def draw(self, _, renderer: Renderer2D):
        x, y, w, h = self.draw_rect

        bg_color = self.clicked_color if self.clicked else self.button_color 
        renderer.draw_rect((x, y, w, h), bg_color)
        renderer.draw_text(self.font, self.text, self.draw_rect.topleft, (1, 1, 1), self.text_scale)

class GUIManager:
    def __init__(self, screen: Screen):
        self.resolution_ptr = pg.Vector2(*screen.get_size())
        self.elements: dict[int, list[GUIElement]] = {}

        self.should_update = False

    def queue_update(self):
        self.should_update = True

    def resize(self, new_width: int, new_height: int):
        "Resize the container and its children elements"
        self.resolution_ptr.x = new_width
        self.resolution_ptr.y = new_height

        for elements in self.elements.values():
            for element in elements:
                element.resize()

    def add_elements(self, *elements: tuple[int, GUIElement]):
        for item in elements:
            assert len(item) == 2, "GUI elements should be added in pairs `(z, element)`"

            z, element = item

            # We need to compute our element's initial rectangle
            element.bind_resolution_ptr(self.resolution_ptr)
            element.resize()

            if z not in self.elements:
                self.elements[z] = []

            self.elements[z].append(element)

    def update(self, resources: Resources):
        "This should be called only when there's actual input from the app"
        
        if not self.should_update:
            return
        self.should_update = False

        input_manager = resources[InputManager]

        for elements in self.elements.values():
            for element in elements:
                element.update(resources, input_manager)

    def draw(self, resources: Resources):
        renderer = resources[Renderer2D]

        sort_func = lambda item: item[0]
        for _, elements in sorted(self.elements.items(), key=sort_func):
            for element in elements:
                element.draw(resources, renderer)

    def clear(self):
        self.elements.clear()

def update_gui(resources: Resources):
    resources[GUIManager].update(resources)

def draw_gui(resources: Resources):
    resources[GUIManager].draw(resources)

def resize_gui(resources: Resources, event: WindowResizeEvent):
    resources[GUIManager].resize(event.new_width, event.new_height)

def queue_update_gui(resources: Resources, _):
    resources[GUIManager].queue_update()

class GUIManagerPlugin(Plugin):
    def build(self, app):
        app.insert_resource(GUIManager(app.get_resource(Screen)))
        app.add_systems(Schedule.Update, update_gui)
        app.add_systems(Schedule.Render, draw_gui)

        app.add_event_listener(MouseMotionEvent, queue_update_gui)
        app.add_event_listener(WindowResizeEvent, resize_gui)