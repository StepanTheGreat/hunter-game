"""
Camera attachment plugin. 
This makes it possible to create multiple cameras, and select one based on priority
"""

from plugin import Resources, Schedule, Plugin

from core.graphics.camera import Camera3D
from core.sound import SoundManager
from core.ecs import component, WorldECS

from plugins.client.components import RenderPosition, RenderAngle

@component
class PerspectiveAttachment:
    """
    A perspective is a combination of both character's visual and audio perception. 
    It's both their camera and ears. The perspective attachment allows an entity to both 
    perceive and hear the surrounding around it. 
    """
    def __init__(self, height: float, priority: int):
        self.height = height
        self.priority = priority

class CurrentPerspectiveAttached:
    "To which entity is the current perspective attached? Useful for ignoring sprites whose pespective is currently active"
    def __init__(self):
        self.attached_entity = None

    def attach_to(self, ent: int):
        "Attach the perspective to the provided entity ID"
        self.attached_entity = ent

    def detach(self):
        "This perspective isn't attached to anything"
        self.attached_entity = None

def move_perspective(resources: Resources):
    world = resources[WorldECS]
    camera = resources[Camera3D]
    sound_manager = resources[SoundManager]
    pespective_attached = resources[CurrentPerspectiveAttached]

    candidates = world.query_component(PerspectiveAttachment, including=(RenderPosition, RenderAngle))
    if len(candidates) == 0:
        pespective_attached.detach()
        return
    
    candiate_ent, attachment = min(candidates, key=lambda candidate: candidate[1].priority)
    position, angle = world.get_components(candiate_ent, RenderPosition, RenderAngle)

    pos = position.get_position()
    
    # First attach our camera
    camera.set_angle(angle.get_angle())
    camera.set_pos(pos)
    camera.set_y(attachment.height)

    # Then our listener
    sound_manager.set_listener_position(pos)

    pespective_attached.attach_to(candiate_ent)

class PerspectivePlugin(Plugin):
    def build(self, app):
        app.insert_resource(CurrentPerspectiveAttached())
        app.add_systems(Schedule.PreDraw, move_perspective)