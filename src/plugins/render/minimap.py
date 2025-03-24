from plugin import Resources, Schedule, Plugin

from modules.entity import EntityContainer


from .map import WorldMap
from .renderer import Renderer2D

from ..entity.player import Player
from ..map import TILE_SIZE

class MinimapPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Render, draw_minimap)

def draw_minimap(resources: Resources):
    wmap = resources[WorldMap]
    renderer = resources[Renderer2D]

    entities = resources[EntityContainer]

    tiles = wmap.get_map().get_tiles()

    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if tile == 0:
                continue
            
            renderer.draw_rect((x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE), (1, 0, 0))
            # collider = make_rect_collider((x*TILE_SIZE, y*TILE_SIZE), (TILE_SIZE, TILE_SIZE), ColliderType.Static, 5)

    player = entities.get_group(Player)[0]
    pos = player.get_pos()
    size = Player.HITBOX_SIZE
    renderer.draw_rect((pos.x-size, pos.y-size, size, size), (0, 1, 0))