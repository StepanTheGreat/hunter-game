from plugin import Resources, Schedule, Plugin

from core.ecs import WorldECS

from plugins.components import Position, RenderPosition
from plugins.collisions import StaticCollider, DynCollider

from plugins.graphics import Renderer2D
from plugins.entities.player import Player

# Remove this constant. A minimap should be a GUI element, not a standalone plugin
MINIMAP_SCALE = 0.5

def draw_minimap(resources: Resources):
    renderer = resources[Renderer2D]
    world = resources[WorldECS]

    scale = MINIMAP_SCALE

    rects = []
    for ent, (pos, collider) in world.query_components(Position, StaticCollider):
        pos = pos.get_position()*scale

        rects.append((
            (pos.x, pos.y, collider.rect.w*scale, collider.rect.h*scale), 
            (0.2, 0.2, 0.2)
        ))

    if rects:
        renderer.draw_rects(rects)

    for ent, (pos, collider) in world.query_components(RenderPosition, DynCollider):
        pos = pos.get_position()*scale
        color = (0, 1, 0) if world.has_component(ent, Player) else (1, 0, 0)
        renderer.draw_circle((pos.x, pos.y), collider.radius*MINIMAP_SCALE, color)

class MinimapPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Draw, draw_minimap)