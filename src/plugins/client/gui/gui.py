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

from plugin import Plugin, Schedule, Resources

from core.time import SystemScheduler

from .widgets import *

from app_config import CONFIG

INPUT_EVENTS = (
    MouseMotionEvent,
    MouseButtonDownEvent,
    MouseButtonUpEvent
)

GUI_Z = 10 # Our GUI starts at Z 10

class GUIManager:
    """
    A GUI manager is simply a globally available SizedBox element, that resizes dynamically based on the screen size.
    Attaching to this element will hook a GUIElement to all rendering/update lifecycles.
    """
    def __init__(self, width: int, height: int, gui_z: int):
        self.document = SizedBox((0, 0), (0, 0), (width, height))
        self.z = gui_z
        "The Z coordinate from which all elements get rendered"

    def attach_elements(self, *elements: GUIElement):
        for element in elements:
            element.attach_to(self.document)

    def clear_elements(self):
        "Remove all elements from the GUI document"
        for child in self.document.get_children():
            child.attach_to(None)

    def detach_elements(self, *elements: GUIElement):
        "Detach all elements from the document."
        for element in elements:
            element.attach_to(None)

    def resize(self, new_width: int, new_height: int):
        "Should be called every time the screen changes its size"
        self.document.set_size(new_width, new_height)

    def draw(self, renderer: Renderer2D):
        "Draw the entire GUI from the root element"
        
        # We will save the Z coordinate, as it we would like to reset it later
        prev_z = renderer.current_z

        # Set our Z coordinate
        renderer.current_z = self.z
        self.document.draw_root(renderer)

        # Reset back
        renderer.current_z = prev_z
    
    def pass_event(self, event: object):
        self.document.on_event_root(event)

class GUIBundleManager:
    """
    A GUI Bundle Manager maintains a simple GUI element list stack that can be useful for scenes.

    Since it operates in layers - it's pretty convenient to add more GUI layers (like a pause menu while ingame),
    without any complex state machinery.
    """

    def __init__(self, scheduler: SystemScheduler, gui: GUIManager):
        self.scheduler = scheduler
        self.gui = gui
        self.gui_elements = []

        self._queued_operations: list[Callable, tuple] = []
        """
        First of all, why do we even need to queue operations on the GUI? Well, they way we handle
        GUI input and callbacks is... we don't have any limits on them. While our GUI elements are
        evaluated - they can freely modify the GUI tree in real time.

        While removing/adding parents is one thing - entirely removing the root (which is what happens
        when we say, pop the current gui layer) causes a lot of undefined behaviour. Most notably:
        the first child losing its parent, thus gaining absolute positioning, and moving to the (0, 0)
        coordinates. Even though we're still processing user input!!

        That's why we're keeping this simple list where... I don't really want to overcomplicate this,
        but for now this list will simply contain private methods to be executed and its arguments.
        """

    def _queue_op(self, method: Callable, *args):
        "Queue an operation on the GUI (essentially a method and its arguments)"

        self._queued_operations.append((method, args))

        # We're going to schedule the flushing of this operation on the next tick.
        # One cool thing about scheduler is that scheduling the same system multiple times simply
        # overwrites it, which means we don't have to construct complex state-machines
        # for efficient late callbacks
        self.scheduler.schedule_ticks(flush_gui_operations, 1)

    def _push_gui(self, new_elements: list[GUIElement]):
        self.gui.attach_elements(*new_elements)
        self.gui_elements.append(new_elements)

    def push_gui(self, new_elements: list[GUIElement]):
        "Push a new GUI layer to the stack"

        self._queue_op(self._push_gui, new_elements)

    def _pop_gui(self):
        if self.gui_elements:
            self.gui.detach_elements(*self.gui_elements.pop())

    def pop_gui(self):
        "Pop a single GUI layer from the stack. Doesn't do anything if the stack is empty"

        self._queue_op(self._pop_gui)

    def _replace_gui(self, new_elements: list[GUIElement]):
        self.pop_gui()
        self.push_gui(new_elements)

    def replace_gui(self, new_elements: list[GUIElement]):
        "Short for `self.pop_gui()` + `self.push_gui(...)`"

        self._queue_op(self._replace_gui, new_elements)

    def _clear(self):
        while self.gui_elements:
            self._pop_gui()

    def clear(self):
        "Clear the entire GUI stack"

        self._queue_op(self._clear)

    def _flush_queued_ops(self):
        "Flush all queued operations on the GUI and clear the buffer"

        for operation, args in self._queued_operations:
            operation(*args)

        self._queued_operations.clear()

def flush_gui_operations(resources: Resources):
    resources[GUIBundleManager]._flush_queued_ops()

def draw_gui(resources: Resources):
    resources[GUIManager].draw(resources[Renderer2D])

def update_gui(resources: Resources, event: object):
    resources[GUIManager].pass_event(event)

def on_screen_resize(resources: Resources, event: WindowResizeEvent):
    resources[GUIManager].resize(event.new_width, event.new_height)

class GUIManagerPlugin(Plugin):
    def build(self, app):
        app.insert_resource(GUIManager(CONFIG.width, CONFIG.height, GUI_Z))
        app.insert_resource(GUIBundleManager(
            app.get_resource(SystemScheduler),
            app.get_resource(GUIManager)
        ))

        app.add_systems(Schedule.Draw, draw_gui, priority=1)
        app.add_event_listener(WindowResizeEvent, on_screen_resize)

        for event_ty in INPUT_EVENTS:
            app.add_event_listener(event_ty, update_gui)

