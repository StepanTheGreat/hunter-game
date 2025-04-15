"""
Stack based GUI system.
This doesn't use stacking inherently, but the key idea behind it is to treat your GUI as boxes stacked on
top (or below) each other.

```
[button1][input]
[button2]
```

In this idea we have a `button1` box, to which we have attached `button2` box below and `input` box to the right.
This is essentially what most GUI libraries do, but here we avoid the concept of a layour container entirely.

This idea allows us to easily model custom GUI elements, recalculate layout, customize layout
direction and so much more.

There are 2 concepts that allow us to "stack" our elements onto another: its edge and pivot coordinates.

## Edges
Edge coordinates while difficult to explain in simple terms, are coordinates that define our inner rectangle area
in range between `0` and `1`.

The top-left corner of a rectangle has an adge `0, 0`, top-right: `1, 0`, bottom-left: `0, 1` and so on.
With these 2 coordinates we can define at which point on the rectangle we would like to place our element. Usually
it should be an edge, but you can also place it inside the parent (though I don't see any reason to do that).

## Anchoring
Anchor or pivot coordinates, are coordinates that define our rectangle's center. If we represent our rectangle size in range
from `0,0` to `1, 1`, our center will be `0.5, 0.5`. This is a highly simple concept, but in combination
with edges we can put our element at ANY position we want.

## Parents/Children
Box stacking doesn't really make sense if we can't stack multiple boxes on top of each other, right?

A root element (without a parent) is positioned at absolute coordinates (in pixels), though their pivot is still
used when centering their rectangle.

Child elements however, are placed based on the attanched parent's box using both their edge and pivot coordinates.

An element can have an unlimited amount of children, but only one parent (or none).

## Nuances
Box stacking, compared to common GUI layout designs like containers has 1 distinct difference:
the size of a child's container doesn't affect the parent's.
In most layout designs a child will always affect the parent's boundary box, but since in our design things like
containers simply don't exist - this is impossible. 

And since containers are non-existent, well... we can't do container things, like say wrapping a background
texture over container items.

There are solutions to this, as we can add simple bubbling-up message passing whenever a child has recalculated
its rectangle and then compute our container's bounding box based on the most distant child coordinates, but, 
even this has some performance cost.
"""

import pygame as pg
import moderngl as gl

from typing import Optional, Callable
from collections import deque

from plugins.graphics.render2d import Renderer2D
from core.graphics import FontGPU

from core.pg.events import *

from plugin import Plugin, Schedule, Resources

INPUT_EVENTS = (
    MouseMotionEvent,
    MouseButtonDownEvent,
    MouseButtonUpEvent
)

class GUIElement:
    """
    The purpose of using GUI elements is to centralize all update and rendering logic into one
    """
    def __init__(self, edge: tuple[float, float], pivot: tuple[float, float]):
        
        self.position: tuple[float, float] = (0, 0)
        "The position that will be used by the element if it doesn't have a parent"

        self.parent: Optional[GUIElement] = None
        "The element to which this element is attached"

        self.children: list[GUIElement] = []
        "The elements that are attached to this element"

        self.__rect: pg.Rect = None
        self.__size: tuple[float, float] = None

        self.margin: tuple[int, int] = (0, 0)
        """
        The offset in pixels from this element that goes (left, top, right, bottom). 
        It doesn't affect the rectangle, but child position calculations instead (it can also stack with the child's margin as well)
        """

        self.hidden: bool = False
        "A hidden element doesn't get drawn, including its children"

        self.pivot: tuple[float, float] = pivot
        self.edge: tuple[float, float] = edge
    
    def set_margin(self, new_x: float, new_y: float):
        self.margin = (new_x, new_y)

        self.recompute_position()

    def with_margin(self, new_x: float, new_y: float):
        self.set_margin(new_x, new_y)
        return self
        
    def with_position(self, x: float, y: float):
        self.set_position(x, y)
        return self
    
    def attached_to(self, to: "GUIElement"):
        self.attach_to(to)
        return self

    def __add_child(self, child: "GUIElement"):
        self.children.append(child)

    def __remove_child(self, child: "GUIElement"):
        try:
            self.children.remove(child)
        except ValueError:
            pass

    def get_parent(self) -> Optional["GUIElement"]:
        return self.parent

    def get_children(self) -> list["GUIElement"]:
        return self.children

    def attach_to(self, parent: Optional["GUIElement"]):
        if self.parent is not None:
            # If we had a parent, we need to remove ourselves from it 
            self.parent.__remove_child(self)

        self.parent = parent

        if self.parent is not None:
            # Of course, if we attach to nothing - we don't need to notify anything
            self.parent.__add_child(self)

        self.recompute_position()

    def get_rect(self) -> pg.Rect:
        return self.__rect.copy()
    
    def __compute_position(self, width: float, height: float) -> tuple[float, float]:
        pivotx, pivoty = self.pivot
        edgex, edgey = self.edge
        
        if self.parent is None:
            assert self.position is not None, "The root element's position must be defined"

            x, y = self.position
            return x - pivotx*width, y - pivoty*height
        else:
            rect = self.parent.get_rect()
            mx, my = self.margin

            return (rect.x+rect.w*edgex) - pivotx*width + mx, (rect.y+rect.h*edgey) - pivoty*height + my
            
    def __compute_rect(self, new_width: float, new_height: float) -> pg.Rect:
        return pg.Rect(
            *self.__compute_position(new_width, new_height), 
            new_width, 
            new_height
        )
    
    def is_root(self) -> bool:
        return self.parent is None
    
    def is_hidden(self) -> bool:
        return self.hidden
    
    def hide(self, to: bool):
        self.hidden = to
    
    def recompute_position(self):
        "Recursively recompute this element's and its childrens' positions"
        self.__rect = self.__compute_rect(*self.__size)

        for child in self.children:
            child.recompute_position()

    def get_position(self) -> tuple[float, float]:
        return self.__rect.topleft
    
    def set_size(self, new_width: float, new_height: float):
        "Update this element's size, while also notifying its children of its new size"
        self.__size = (new_width, new_height)
        self.recompute_position()

    def set_position(self, x: float, y: float):
        "This is essentially the same as `set_size`, but for changing element's position"
        assert self.is_root(), "Can't set a position on child elements"
        
        self.position = (x, y)
        self.set_size(*self.__size)

    def set_tree_position(self, x: float, y: float, pivot: tuple[float, float] = (0, 0)):
        """
        Change the position of the entire tree rectangle. Essentially it will measure the tree size,
        then update the root's position. Using pivot you can apply additional transformations
        like centering the tree.
        """

        assert self.is_root(), "Only root elements support tree positioning"

        pivot_x, pivot_y = pivot
        _, _, tree_w, tree_h = self.measure_tree()
        self.set_position(x-tree_w*pivot_x, y-tree_h*pivot_y)

    def draw(self, renderer: Renderer2D):
        "Element's draw logic"

    def on_event(self, event: object):
        "Element's custom logic whenever an input event is dispatched"
    
    def call_root(self, f: Callable[["GUIElement"], bool]):
        """
        Call a user function on the entire tree in breadth-first order. 
        The function must return `True` in order to stop processing further node's children.

        So if for example a node A is getting processed with its children B and C, and the function
        with node A returns `True` - its children will not get processed. If however `False` or `None` is returned - they
        will.
        """

        assert self.is_root(), "A child is not a root GUI element"

        queue = deque([self])

        while len(queue) > 0:
            element = queue.popleft()

            if f(element) != True:
                queue += element.get_children()

    def measure_tree(self, including_hidden: bool = False) -> tuple[float, ...]:
        "Compute an absolute rectangle of the entire tree"
        rect = self.get_rect()
        rect = [*rect.topleft, *rect.bottomright]

        def overwrite_func(element: GUIElement):
            if not including_hidden and element.is_hidden():
                return True
            
            x, y, w, h = element.get_rect()
            if x < rect[0]:
                rect[0] = x
            if y < rect[1]:
                rect[1] = y
            if x+w > rect[2]:
                rect[2] = x+w
            if y+h > rect[3]:
                rect[3] = y+h
            
        self.call_root(overwrite_func)

        return (rect[0], rect[1], rect[2]-rect[0], rect[3]-rect[1])

    def draw_root(self, renderer: Renderer2D):
        "Draw the box tree"
        def draw_element(element: GUIElement):
            if element.is_hidden():
                return True
            
            element.draw(renderer)
        
        self.call_root(draw_element)

    def on_event_root(self, event: object):
        "Pass an input event across the box tree"
        def pass_event(element: GUIElement):
            if element.is_hidden():
                return True
            
            element.on_event(event)

        self.call_root(pass_event)

class ColorRect(GUIElement):
    "A rectangle that is filled with color"
    def __init__(self, edge, pivot, size: tuple[float, float], color: tuple[float, ...]):
        super().__init__(edge, pivot)

        self.color = color
        self.size = size
        self.set_size(*size)

    def draw(self, renderer):
        x, y, w, h = self.get_rect()
        renderer.draw_rect((x, y, w, h), self.color)

class TextureRect(GUIElement):
    "A texture element"
    def __init__(self, edge, pivot, size: tuple[float, float], texture: gl.Texture):
        super().__init__(edge, pivot)

        self.texture = texture
        self.color = (1, 1, 1)
        self.size = size
        self.uv_rect = (0, 0, 1, 1)
        self.set_size(*size)

    def draw(self, renderer):
        x, y, w, h = self.get_rect()
        renderer.draw_texture(self.texture, (x, y), (w, h), self.color, self.uv_rect)

class Label(GUIElement):
    def __init__(
            self, 
            font: FontGPU, 
            text: str, 
            edge: tuple[float, float], 
            pivot: tuple[float, float] = (0, 0),
            text_scale: float = 1
        ):
        super().__init__(edge, pivot)
        self.font = font
        self.text = None
        self.text_scale = text_scale

        self.set_text(text)

    def set_text_scale(self, new_scale: float):
        self.text_scale = new_scale
        self.set_text(self.text)

    def set_text(self, text: str):
        self.text = text

        textw, texth = self.font.measure(self.text)
        self.set_size(textw*self.text_scale, texth*self.text_scale)

    def draw(self, renderer):
        renderer.draw_text(self.font, self.text, self.get_position(), (1, 1, 1), self.text_scale)

class BaseButton(GUIElement):
    "Not a user class, instead a super class for other button implementations"
    def __init__(self, edge: tuple[float, float], pivot: tuple[float, float], size: tuple[float, float]):
        assert size[0] > 0 and size[1] > 0, "Button's size can't be 0"

        super().__init__(edge, pivot)

        self.clicked = False
        self.immediate = True
        self.callback: Callable[[], None] = None

    def __call_callback(self):
        if self.callback is not None:
            self.callback()

    def set_callback(self, f: Callable[[], None]):
        self.callback = f

    def with_callback(self, f: Callable[[], None]):
        self.set_callback(f)
        return self

    def set_immediate(self, to: bool):
        """
        A button is immediate when pressing on it will immediately trigger a callback action 
        (without waiting for the mouse button to get released).

        It makes the UI highly responsive, but might not be good for buttons where the user might want to 
        change their mind (shops for example).
        """
        self.immediate = to
    
    def as_immediate(self, to: bool):
        self.set_immediate(to)
        return self

    def on_event(self, event):
        rect = self.get_rect()

        if not self.clicked and type(event) == MouseButtonDownEvent:
            if rect.collidepoint((event.x, event.y)):
                if self.immediate:
                    self.__call_callback()
                self.clicked = True
        elif self.clicked and type(event) == MouseButtonUpEvent:
            if rect.collidepoint((event.x, event.y)):
                if not self.immediate:
                    self.__call_callback()
            self.clicked = False

class TextButton(BaseButton):
    "A clickable rectangle with custom text and background"
    def __init__(
            self, 
            font: FontGPU, 
            text: str, 
            edge: tuple[float, float], 
            size: tuple[float, float],
            pivot: tuple[float, float] = (0, 0),
            text_scale: float = 1
        ):
        super().__init__(edge, pivot, size)
        self.font = font
        self.text = None
        self.text_scale = text_scale
        
        self.text_size = None
        self.size = size

        self.set_size(*self.size)
        self.set_text(text)

    def set_text_scale(self, new_scale: float):
        self.text_scale = new_scale
        self.set_text(self.text)

    def set_text(self, text: str):
        # This method is a bit confusing, but it will try to measure the size of the text
        # and find the largest possible text scale that wouldn't overflow the button's bounding rectangle
        # for said text
        self.text = text
        text_w, text_h = self.font.measure(self.text)

        self.text_scale = min(
            min(self.size[0]/text_w, self.size[1]/text_h),
            # Select the smallest axis fraction, which guarantees that the text will fit   

            self.text_scale, 
            # Or if the requested text scale is smaller - we can choose it instead
        )

        self.text_size = (text_w*self.text_scale, text_h*self.text_scale)

    def draw(self, renderer):
        rect = self.get_rect()
        
        bg_color = (0.2, 0.2, 0.2) if self.clicked else (0.4, 0.4, 0.4)

        renderer.draw_rect((rect.x, rect.y, rect.w, rect.h), bg_color)

        text_w, text_h = self.text_size
        size_w, size_h = self.size

        renderer.draw_text(
            self.font, 
            self.text, 
            (rect.x+size_w/2-text_w/2, rect.y+size_h/2-text_h/2), 
            (1, 1, 1), 
            self.text_scale
        )

class TextureButton(BaseButton):
    "A really primitive version of `TextButton`. Simpler and faster for image-only buttons"
    def __init__(
            self, 
            texture: gl.Texture,
            edge: tuple[float, float], 
            size: tuple[float, float],
            pivot: tuple[float, float] = (0, 0),
        ):
        super().__init__(edge, pivot, size)
        self.size = size
        self.texture = texture
        self.uv_rect = (0, 0, 1, 1)
        self.color = (1, 1, 1)

        self.set_size(*self.size)

    def draw(self, renderer):
        rect = self.get_rect()
        renderer.draw_texture(self.texture, (rect.x, rect.y), (rect.w, rect.h), self.color, self.uv_rect)

class Slider(GUIElement):
    "A slidable rectangle that produces values between 0 and 1"
    def __init__(self, edge, pivot, size: tuple = (128, 8), slider_height: float = 8, default_value: float = 0):
        super().__init__(edge, pivot)

        self.sliding = False

        self.value = default_value
        self.size = size
        self.slider_height = slider_height
        self.set_size(*self.size)

    def on_event(self, event):
        rect = self.get_rect()

        if self.sliding and type(event) == MouseMotionEvent:
            x_pos = max(rect.x, min(rect.x+rect.w, event.x))
            self.value = (x_pos-rect.x)/rect.w
        elif not self.sliding and type(event) == MouseButtonDownEvent:
            if rect.collidepoint((event.x, event.y)):
                self.sliding = True
                x_pos = max(rect.x, min(rect.x+rect.w, event.x))
                self.value = (x_pos-rect.x)/rect.w
        elif self.sliding and type(event) == MouseButtonUpEvent:
            self.sliding = False

    def draw(self, renderer):
        rect = self.get_rect()

        value = self.value
        slider_h = self.slider_height
        vertical_offset = (rect.h-slider_h)/2
        renderer.draw_rect((rect.x, rect.y+vertical_offset, rect.w, slider_h), (0.2, 0.2, 0.2))
        renderer.draw_circle((rect.x+value*rect.w, rect.centery), self.size[1], (1, 0, 0), 10)

class GUIManager:
    def __init__(self):
        self.elements: list[GUIElement] = []

    def add_elements(self, *elements: GUIElement):
        for element in elements:
            self.elements.append(element)

    def clear_elements(self):
        "Remove all elements from the GUI manager"
        self.elements.clear()

    def remove_elements(self, *elements: GUIElement):
        for element in elements:
            try:
                self.elements.remove(element)
            except ValueError:
                pass

    def draw(self, renderer: Renderer2D):
        for root_element in self.elements:
            root_element.draw_root(renderer)
    
    def pass_event(self, event: object):
        for root_element in self.elements:
            root_element.on_event_root(event)

def draw_gui(resources: Resources):
    resources[GUIManager].draw(resources[Renderer2D])

def update_gui(resources: Resources, event: object):
    resources[GUIManager].pass_event(event)

class GUIManagerPlugin(Plugin):
    def build(self, app):
        app.insert_resource(GUIManager())
        app.add_systems(Schedule.Draw, draw_gui, priority=1)

        for event_ty in INPUT_EVENTS:
            app.add_event_listener(event_ty, update_gui)

