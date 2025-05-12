from plugins.shared.entities.characters import *
from plugins.client.components import *

from plugins.shared.interfaces.map import MapCamera
    
CAMERA_PERSPECTIVE_PRIORITY = 10
"It's probably the last perspective we would like to see"

def make_map_camera(camera: MapCamera) -> tuple:
    "A map camera is an empty entity that simply looks in a specific direction"

    components = (
        Position(*camera.pos),
        RenderPosition(),
        RenderAngle(),
        Angle(camera.angle),
        AngleVelocity(1, camera.angle_vel),
        PerspectiveAttachment(camera.height, CAMERA_PERSPECTIVE_PRIORITY),
        Camera()
    )

    return components