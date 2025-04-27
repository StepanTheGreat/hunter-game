"""
Camera attachment plugin. 
This makes it possible to create multiple cameras, and select one based on priority
"""

from plugin import Resources, Schedule, Plugin

from core.graphics.camera import Camera3D
from core.ecs import component, WorldECS

from plugins.components import RenderPosition, RenderAngle

@component
class Camera3DAttachment:
    """
    A 3D camera attachment with priority. 
    The smaller the priority - the more priority it has. Sorry if this doesn't make any sense
    """
    def __init__(self, height: float, priority: int):
        self.height = height
        self.priority = priority

class CurrentCameraAttached:
    "To which entity is the current camera attached? Useful for ignoring sprites whose camera's are currently active"
    def __init__(self):
        self.attached_entity = None

    def attach_to(self, ent: int):
        "Attach the camera to the provided entity ID"
        self.attached_entity = ent

    def detach(self):
        "This camera isn't attached to anything"
        self.attached_entity = None

def move_camera(resources: Resources):
    world = resources[WorldECS]
    camera = resources[Camera3D]
    camera_attached = resources[CurrentCameraAttached]

    candidates = world.query_component(Camera3DAttachment, including=(RenderPosition, RenderAngle))
    if len(candidates) == 0:
        camera_attached.detach()
        return
    
    candiate_ent, attachment = min(candidates, key=lambda candidate: candidate[1].priority)
    position, angle = world.get_components(candiate_ent, RenderPosition, RenderAngle)

    camera.set_angle(angle.get_angle())
    camera.set_pos(position.get_position())
    camera.set_y(attachment.height)
    camera_attached.attach_to(candiate_ent)

class CameraAttachmentPlugin(Plugin):
    def build(self, app):
        app.insert_resource(CurrentCameraAttached())
        app.add_systems(Schedule.PreDraw, move_camera)