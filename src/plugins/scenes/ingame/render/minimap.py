from plugin import Resources, Schedule, Plugin, run_if, resource_exists

from core.entity import EntityWorld

from plugins.graphics import Renderer2D
from plugins.entities.player import Player
from plugins.entities.sprite import Sprite

from modules.tilemap import WorldMap

# Remove this constant. A minimap should be a GUI element, not a standalone plugin
TILE_SIZE = 48
MINIMAP_SCALE = 0.5

@run_if(resource_exists, WorldMap)
def draw_minimap(resources: Resources):
    wmap = resources[WorldMap]
    renderer = resources[Renderer2D]

    entities = resources[EntityWorld]

    tiles = wmap.get_map().get_tiles()
    scale = MINIMAP_SCALE

    offsetx, offsety = wmap.get_offset()

    tile_size = TILE_SIZE * scale
    player_size = Player.HITBOX_SIZE * scale
    sprite_size = Sprite.HITBOX_SIZE * scale

    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            posx, posy = offsetx+x, offsety+y
            if tile != 0:
                renderer.draw_rect((posx*tile_size, posy*tile_size, tile_size, tile_size), (0.2, 0.2, 0.2))

    players = entities.get_group(Player)
    if len(players) > 0:
        player = players[0]
        pos = player.get_pos()/TILE_SIZE*tile_size
        renderer.draw_circle((pos.x, pos.y), player_size, (0, 1, 0))

    for sprite in entities.get_group(Sprite):
        pos = sprite.pos.copy()/TILE_SIZE*tile_size
        renderer.draw_circle((pos.x, pos.y), sprite_size, (1, 0, 0))

class MinimapPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Render, draw_minimap)