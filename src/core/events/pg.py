import pygame as pg
from plugin import event

@event
class PygameEvent:
    "Basically the same as `pygame.Event`, but registered for all pygame events that don't have a direct mapping"
    def __init__(self, event: pg.event.Event):
        self.type = event.type
        self.dict = event.dict

@event
class WindowResizeEvent:
    "Fired when window's resolution gets changed"
    def __init__(self, event: pg.event.Event):
        self.new_width = event.w
        self.new_height = event.h

@event
class MouseMotionEvent:
    "The mouse has moved"
    def __init__(self, event: pg.event.Event):
        self.x = event.pos[0]
        self.y = event.pos[1]

@event
class MouseButtonDownEvent:
    "The mouse button is down"
    def __init__(self, event: pg.event.Event):
        self.x = event.pos[0]
        self.y = event.pos[1]
        self.button = event.button

@event
class MouseButtonUpEvent:
    "The mouse button is up"
    def __init__(self, event: pg.event.Event):
        self.x = event.pos[0]
        self.y = event.pos[1]
        self.button = event.button

@event
class QuitEvent:
    "An event that gets fired when the user would like to quit. This will stop the entire application"
    def __init__(self, _):
        pass