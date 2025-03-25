from plugin import Resources, Schedule, Plugin

from modules.entity import EntityContainer


from .map import WorldMap
from .renderer import Renderer2D

from ..entity.player import Player
from ..entity.sprite import Sprite

from ..map import TILE_SIZE

MINIMAP_SCALE = 0.5

class MinimapPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Render, draw_minimap)

def draw_minimap(resources: Resources):
    wmap = resources[WorldMap]
    renderer = resources[Renderer2D]

    entities = resources[EntityContainer]

    tiles = wmap.get_map().get_tiles()
    scale = MINIMAP_SCALE

    tile_size = TILE_SIZE * scale
    player_size = Player.HITBOX_SIZE * scale
    sprite_size = Sprite.HITBOX_SIZE * scale

    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if tile != 0:
                renderer.draw_rect((x*tile_size, y*tile_size, tile_size, tile_size), (0.2, 0.2, 0.2))

    player = entities.get_group(Player)[0]
    pos = player.get_pos()/TILE_SIZE*tile_size
    renderer.draw_circle((pos.x, pos.y), player_size, (0, 1, 0))

    for sprite in entities.get_group(Sprite):
        pos = sprite.pos.copy()/TILE_SIZE*tile_size
        renderer.draw_circle((pos.x, pos.y), sprite_size, (1, 0, 0))