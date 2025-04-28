from plugin import Resources, Schedule, Plugin

from core.ecs import WorldECS
from core.pg import Screen

from plugins.components import Position, RenderPosition
from plugins.collisions import StaticCollider, DynCollider

from plugins.graphics import Renderer2D
from plugins.entities.player import Player

# Remove this constant. A minimap should be a GUI element, not a standalone plugin
MINIMAP_SCALE = 0.5

def draw_minimap(resources: Resources):
    renderer = resources[Renderer2D]
    screen = resources[Screen]
    world = resources[WorldECS]

    width, height = screen.get_size()

    scale = MINIMAP_SCALE

    rects, circles = [], []
    for ent, (pos, collider) in world.query_components(Position, StaticCollider):
        x, y = pos.get_position()*scale
        w, h = collider.rect.w*scale, collider.rect.h*scale

        if (x+w >= 0 and x < width) and (y+h >= 0 and y < height):
            rects.append((
                (x, y, w, h), 
                (40, 40, 40)
            ))

    for ent, (pos, collider) in world.query_components(RenderPosition, DynCollider):
        x, y = pos.get_position()*scale
        r = collider.radius*MINIMAP_SCALE

        if (x+r >= 0 and x < width) and (y+r >= 0 and y < height):
            color = (0, 255, 0) if world.has_component(ent, Player) else (255, 0, 0)

            circles.append((
                (x, y), r, color
            ))
    
    if rects:
        renderer.draw_rects(rects)
    if circles:
        renderer.draw_circles(circles)

class MinimapPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Draw, draw_minimap)