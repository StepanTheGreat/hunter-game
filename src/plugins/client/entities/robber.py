from plugin import Plugin, Resources, Schedule

from plugins.client.graphics.lights import Light
from plugins.client.perspective import PerspectiveAttachment

from plugins.client.components import *
from plugins.shared.entities.robber import make_robber
    
def make_client_robber(uid: int, pos: tuple[float, float]) -> tuple:
    return make_robber(uid, pos) + (
        RenderPosition(),
        RenderAngle(),
        PerspectiveAttachment()
    )

class ClientRobberPlugin(Plugin):
    def build(self, app):
        pass