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

from core.time import Clock
from core.events.pg import *

from plugins.client.interfaces.gui_widgets import *
from plugins.client.commands.gui import *

from ..graphics.render2d import Renderer2D

from app_config import CONFIG

from typing import Union

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

    def draw(self, renderer: Renderer2D, dt: float):
        "Draw the entire GUI from the root element"
        
        # We will save the Z coordinate, as it we would like to reset it later
        prev_z = renderer.current_z

        # Set our Z coordinate
        renderer.current_z = self.z
        self.document.draw_root(renderer, dt)

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

    def __init__(self, gui: GUIManager):
        self.gui = gui
        self.gui_elements = []

    def _push_gui(self, new_elements: list[GUIElement]):
        self.gui.attach_elements(*new_elements)
        self.gui_elements.append(new_elements)

    def _pop_gui(self):
        if self.gui_elements:
            self.gui.detach_elements(*self.gui_elements.pop())

    def _replace_gui(self, new_elements: list[GUIElement]):
        self._pop_gui()
        self._push_gui(new_elements)

    def _clear(self):
        while self.gui_elements:
            self._pop_gui()


def draw_gui(resources: Resources):
    dt = resources[Clock].get_delta()

    resources[GUIManager].draw(resources[Renderer2D], dt)

def update_gui(resources: Resources, event: object):
    resources[GUIManager].pass_event(event)

def on_screen_resize(resources: Resources, event: WindowResizeEvent):
    resources[GUIManager].resize(event.new_width, event.new_height)

def on_gui_command(resources: Resources, event: Union[PushGUICommand, PopGUICommand, ReplaceGUICommand, ClearGUICommand]):
    "Handle the GUI commands"

    gui_manager = resources[GUIBundleManager]

    event_ty = type(event)
    if event_ty is PushGUICommand:
        gui_manager._push_gui(event.new_elements)
    elif event_ty is PopGUICommand:
        gui_manager._pop_gui()
    elif event_ty is ReplaceGUICommand:
        gui_manager._replace_gui(event.new_elements)
    else:
        gui_manager._clear()

class GUIManagerPlugin(Plugin):
    def build(self, app):
        app.insert_resource(GUIManager(CONFIG.width, CONFIG.height, GUI_Z))
        app.insert_resource(GUIBundleManager(app.get_resource(GUIManager)))

        app.add_systems(Schedule.Draw, draw_gui, priority=1)
        app.add_event_listener(WindowResizeEvent, on_screen_resize)

        # Handle all our different GUI control commands
        for event_ty in (PushGUICommand, PopGUICommand, ReplaceGUICommand, ClearGUICommand):
            app.add_event_listener(event_ty, on_gui_command)

        # Connect to usual pygame events
        for event_ty in INPUT_EVENTS:
            app.add_event_listener(event_ty, update_gui)

