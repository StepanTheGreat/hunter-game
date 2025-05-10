from plugin import Resources, EventWriter

from core.assets import AssetManager
from core.graphics import FontGPU

from plugins.client.interfaces.gui import GUIElement, TextButton
from plugins.client.services.playerstats import PlayerStats

from plugins.client.commands import ClearGUICommand, ReplaceGUICommand

from plugins.client.actions import ClientActionDispatcher, SignalPlayerReadyAction

class PlayerHealthbar(GUIElement):
    BG_COLOR = (40, 40, 40)
    HEALTH_COLOR = (40, 255, 70)
    def __init__(
        self, 
        edge: tuple[int, int], 
        pivot: tuple[int, int], 
        size: tuple[int, int], 
        bar_margin: int, 
        player_stats: PlayerStats,
        margin: tuple[int, int] = (0, 0), 
    ):
        super().__init__(edge, pivot)

        self.stats: PlayerStats = player_stats

        self.bar_margin = bar_margin
        self.set_size(*size)
        self.set_margin(*margin)

    def draw(self, renderer):
        x, y, w, h = self.get_rect()
        m = self.bar_margin

        renderer.draw_rect((x, y, w, h), PlayerHealthbar.BG_COLOR)

        health_w, health_h = w-m*2, h-m*2
        health_x, health_y = x+m, y+m

        frac = self.stats.get_health()
        rfrac = 1-frac
        renderer.draw_rect((
            health_x+rfrac*health_w, 
            health_y, 
            health_w*frac, 
            health_h
        ), PlayerHealthbar.HEALTH_COLOR)

class IngameGUI:
    BUTTON_SIZE = (312, 64)

    def __init__(self, resources: Resources):
        self.resources = resources
        self.ewriter = resources[EventWriter]
        self.assets = resources[AssetManager]
        self.dispatcher = resources[ClientActionDispatcher]

        self.ewriter.push_event(ClearGUICommand())
        self.enter_ingame()

    def enter_ingame(self):
        font = self.assets.load(FontGPU, "fonts/font.ttf")

        healthbar = PlayerHealthbar((1, 0), (1, 0), (260, 32), 6, self.resources[PlayerStats])

        is_ready: list[bool] = [False]

        ready_btn = TextButton(font, "I'm not ready", (0.5, 0.5), (96, 48), (0.5, 0.5), 0.4)

        def change_ready():
            is_ready[0] = not is_ready[0]
            ready_btn.set_text("I'm ready" if is_ready[0] else "I'm not ready")
            self.dispatcher.dispatch_action(SignalPlayerReadyAction(is_ready[0]))
        
        ready_btn.set_callback(change_ready)

        self.ewriter.push_event(ReplaceGUICommand([healthbar, ready_btn]))
