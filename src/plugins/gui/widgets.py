import moderngl as gl

from typing import Optional, Callable
from collections import deque

from plugins.graphics.render2d import Renderer2D

from core.graphics import FontGPU
from core.pg.events import *

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

        self._rect: pg.Rect = None
        self._size: tuple[float, float] = None

        self._margin: tuple[int, int] = (0, 0)
        """
        The offset in pixels from this element that goes (left, top, right, bottom). 
        It doesn't affect the rectangle, but child position calculations instead (it can also stack with the child's margin as well)
        """

        self.hidden: bool = False
        "A hidden element doesn't get drawn, including its children"

        self.pivot: tuple[float, float] = pivot
        self.edge: tuple[float, float] = edge
    
    def set_margin(self, new_x: float, new_y: float):
        self._margin = (new_x, new_y)

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

    def _add_child(self, child: "GUIElement"):
        self.children.append(child)

    def _remove_child(self, child: "GUIElement"):
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
            self.parent._remove_child(self)

        self.parent = parent

        if self.parent is not None:
            # Of course, if we attach to nothing - we don't need to notify anything
            self.parent._add_child(self)

        self.recompute_position()

    def get_rect(self) -> pg.Rect:
        return self._rect.copy()
    
    def _compute_position(self, width: float, height: float) -> tuple[float, float]:
        pivotx, pivoty = self.pivot
        edgex, edgey = self.edge
        
        if self.parent is None:
            assert self.position is not None, "The root element's position must be defined"

            x, y = self.position
            return x - pivotx*width, y - pivoty*height
        else:
            rect = self.parent.get_rect()
            mx, my = self._margin

            return (rect.x+rect.w*edgex) - pivotx*width + mx, (rect.y+rect.h*edgey) - pivoty*height + my
            
    def _compute_rect(self, new_width: float, new_height: float) -> pg.Rect:
        return pg.Rect(
            *self._compute_position(new_width, new_height), 
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
        self._rect = self._compute_rect(*self._size)

        for child in self.children:
            child.recompute_position()

    def get_position(self) -> tuple[float, float]:
        return self._rect.topleft
    
    def set_size(self, new_width: float, new_height: float, recompute: bool = True):
        "Update this element's size, while also notifying its children of its new size"
        self._size = (new_width, new_height)
        if recompute:
            self.recompute_position()

    def set_position(self, x: float, y: float):
        "This is essentially the same as `set_size`, but for changing element's position"
        assert self.is_root(), "Can't set a position on child elements"
        
        self.position = (x, y)
        self.set_size(*self._size)

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

class SizedBox(GUIElement):
    "An empty box element that can be used either for your own custom panels or for the screen itself"
    def __init__(self, edge, pivot, size: tuple[float, float]):
        super().__init__(edge, pivot)        
        self.set_size(*size)

class FillBox(GUIElement):
    """
    A fillbox is a box that will try to take the full space of its parent if present. 
    It's highly useful for backgrounds or resizable panels.
    """
    def __init__(self):
        super().__init__((0, 0), (0, 0))   
    
    def recompute_position(self):
        self.consume_available_space()
        super().recompute_position()

    def consume_available_space(self):
        parent = self.get_parent()
        if parent is None:
            self.set_size(0, 0, False)
        else:
            *_, w, h = parent.get_rect()
            self.set_size(w, h, False)

class ColorRect(FillBox):
    "A rectangle that is filled with color"
    def __init__(self, color: tuple[int, ...]):
        super().__init__()
        self.color = color
        
    def draw(self, renderer):
        x, y, w, h = self.get_rect()
        renderer.draw_rect((x, y, w, h), self.color)

class TextureRect(FillBox):
    "A texture element"
    def __init__(self, texture: gl.Texture):
        super().__init__()

        self.texture = texture
        self.color = (255, 255, 255)
        self.uv_rect = (0, 0, 1, 1)

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
            color: tuple[int, int, int] = (255, 255, 255),
            text_scale: float = 1
        ):
        super().__init__(edge, pivot)
        self.font = font
        self.text = None
        self.text_scale = text_scale
        self.color = color

        self._cached_drawcall = None

        self.set_text(text)

    def set_text_scale(self, new_scale: float):
        self.text_scale = new_scale
        self.set_text(self.text)

    def set_text(self, text: str, force: bool = False):
        if self.text == text and not force:
            return
        self.text = text

        textw, texth = self.font.measure(self.text)
        self.set_size(textw*self.text_scale, texth*self.text_scale)
        self._cached_drawcall = None

    def draw(self, renderer):
        if not self._cached_drawcall:
            self._cached_drawcall = renderer.draw_text_call(self.font, self.text, self.get_position(), self.color, self.text_scale)
        renderer.push_draw_call(self._cached_drawcall)

class BaseButton(GUIElement):
    "Not a user class, instead a super class for other button implementations"
    def __init__(self, edge: tuple[float, float], pivot: tuple[float, float], size: tuple[float, float]):
        assert size[0] > 0 and size[1] > 0, "Button's size can't be 0"

        super().__init__(edge, pivot)

        self.clicked = False
        self.immediate = True
        self.callback: Callable[[], None] = None

    def _call_callback(self):
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
                    self._call_callback()
                self.clicked = True
        elif self.clicked and type(event) == MouseButtonUpEvent:
            if rect.collidepoint((event.x, event.y)):
                if not self.immediate:
                    self._call_callback()
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
        
        bg_color = (40, 40, 40) if self.clicked else (100, 100, 100)

        renderer.draw_rect((rect.x, rect.y, rect.w, rect.h), bg_color)

        text_w, text_h = self.text_size
        size_w, size_h = self.size

        renderer.draw_text(
            self.font, 
            self.text, 
            (rect.x+size_w/2-text_w/2, rect.y+size_h/2-text_h/2), 
            (255, 255, 255), 
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
        self.color = (255, 255, 255)

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
        renderer.draw_rect((rect.x, rect.y+vertical_offset, rect.w, slider_h), (40, 40, 40))
        renderer.draw_circle((rect.x+value*rect.w, rect.centery), self.size[1], (255, 0, 0), 10)