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

from typing import Optional

from collections import deque

from plugins.graphics.render2d import Renderer2D
from core.graphics import FontGPU

from plugin import Plugin, Schedule, Resources

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

        self.pivot: tuple[float, float] = pivot
        self.edge: tuple[float, float] = edge

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

            return (rect.x+rect.w*edgex) - pivotx*width, (rect.y+rect.h*edgey) - pivoty*height
            
    def __compute_rect(self, new_width: float, new_height: float) -> pg.Rect:
        return pg.Rect(
            *self.__compute_position(new_width, new_height), 
            new_width, 
            new_height
        )
    
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
        assert self.parent is None, "Can't set a position on child elements"
        
        self.position = (x, y)
        self.set_size(*self.__size)

    def draw(self, renderer: Renderer2D):
        "Element's draw logic"
            
    def draw_root(self, renderer: Renderer2D):
        assert self.parent is None, "A child is not a root GUI element"

        queue = deque([self])

        while len(queue) > 0:
            element = queue.popleft()
            element.draw(renderer)

            queue += element.get_children()

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

class GUIManager:
    def __init__(self):
        self.elements: list[GUIElement] = []

    def add_elements(self, *elements: GUIElement):
        for element in elements:
            self.elements.append(element)

    def draw(self, renderer: Renderer2D):
        for root_element in self.elements:
            root_element.draw_root(renderer)

def draw_gui(resources: Resources):
    resources[GUIManager].draw(resources[Renderer2D])

class GUIManagerPlugin(Plugin):
    def build(self, app):
        app.insert_resource(GUIManager())
        app.add_systems(Schedule.Draw, draw_gui)

        # We will just make it so every single input event will wakeup our GUI
        # for event_ty in WAKEUP_EVENTS:
        #     app.add_event_listener(event_ty, queue_update_gui)

        # app.add_event_listener(WindowResizeEvent, resize_gui)


