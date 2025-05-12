from plugin import Plugin, Resources, EventWriter, resource_exists, run_if

from core.assets import AssetManager
from core.graphics import FontGPU, Texture
from core.time import SystemScheduler

from plugins.client.interfaces.gui_widgets import GUIElement, TextButton, Label, TextureRect
from plugins.client.services.playerstats import PlayerStats
from plugins.shared.services.network import Client, clean_network_actors

from plugins.client.commands import ClearGUICommand, ReplaceGUICommand, CheckoutSceneCommand, CheckoutScene
from plugins.client.events import ServerDisonnectedEvent
from plugins.client.actions import ClientActionDispatcher, SignalPlayerReadyAction

from plugins.client.commands import PlayersReadyCommand, GameNotificationCommand, GameNotification

GO_BACK_TO_MENU_IN = 8
"The amount of time to wait during the victory stage to automatically go back"

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


        self.font = self.assets.load(FontGPU, "fonts/font.ttf")

        def on_quit():
            if Client in self.resources:
                clean_network_actors(self.resources, Client)

        self.quit_btn = TextButton(self.font, "Quit", (0, 0), (128, 64), (0, 0), 0.3)
        self.quit_btn.set_callback(on_quit)

        self.healthbar = PlayerHealthbar((1, 0), (1, 0), (260, 32), 6, self.resources[PlayerStats])
        self.players_ready_label = Label(self.font, "Players ready: 0/0", (0.5, 1), (0.5, 1), (255, 255, 255), 0.3)

        self.crosshair = TextureRect(
            self.assets.load(Texture, "images/sprites.atl#crosshair"),
            (32, 32),
            (0.5, 0.5),
            (0.5, 0.5)
        )

        self.ewriter.push_event(ClearGUICommand())
        self.enter_waiting_stage()

    def enter_waiting_stage(self):

        # Give me a medal, for the cheapest architectural workaround ever found
        is_ready: list[bool] = [False]

        ready_btn = TextButton(self.font, "I'm not ready", (0.5, 0.5), (168, 84), (0.5, 0.5), 0.4)

        def change_ready():
            is_ready[0] = not is_ready[0]
            ready_btn.set_text("I'm ready" if is_ready[0] else "I'm not ready")
            self.dispatcher.dispatch_action(SignalPlayerReadyAction(is_ready[0]))
        
        ready_btn.set_callback(change_ready)

        self.ewriter.push_event(ReplaceGUICommand([ 
            ready_btn,
            self.players_ready_label,
            self.quit_btn
        ]))

    def enter_game_stage(self):
        self.ewriter.push_event(ReplaceGUICommand([
            self.healthbar,
            self.quit_btn,
            self.crosshair
        ]))

    def enter_finish_stage(self, policemen_won: bool):

        text = "The policemen won!" if policemen_won else "The robster won!"
        color = (100, 100, 255) if policemen_won else (255, 100, 00)
        victory_label = Label(self.font, text, (0.5, 0.5), (0.5, 0.5), color, 0.4) 

        self.ewriter.push_event(ReplaceGUICommand([
            self.healthbar,
            self.crosshair,
            victory_label
        ]))

    def update_players_ready(self, ready: int, players: int):
        self.players_ready_label.set_text(f"Players ready: {ready}/{players}")

@run_if(resource_exists, IngameGUI)
def on_server_disconnection(resources: Resources, _: ServerDisonnectedEvent):
    "When our client is disconnected, we would like to get back to the main menu"

    scheduler = resources[SystemScheduler]

    # Because it's 100% possible for this handler to get called WHEN the system is waiting to be executed,
    # we're going to remove it in advace, so we're not quitting multiple times 
    scheduler.remove_scheduled(go_back_to_menu)

    go_back_to_menu(resources)

@run_if(resource_exists, IngameGUI)
def on_players_ready_command(resources: Resources, command: PlayersReadyCommand):
    gui = resources[IngameGUI]
    gui.update_players_ready(command.players_ready, command.players)

@run_if(resource_exists, IngameGUI)
def on_game_notification(resources: Resources, command: GameNotificationCommand):
    gui = resources[IngameGUI]
    scheduler = resources[SystemScheduler]

    # When we receive a game started notification - we would like to change the curent UI state
    if command.notification == GameNotification.GameStarted:
        gui.enter_game_stage()
    if command.notification in (GameNotification.PolicemenWon, GameNotification.RobberWon):
        policemen_won = command.notification == GameNotification.PolicemenWon

        gui.enter_finish_stage(policemen_won)
        scheduler.schedule_seconds(go_back_to_menu, GO_BACK_TO_MENU_IN, False)

def go_back_to_menu(resources: Resources):
    """
    This system is only called either by callbacks (when disconnected) or scheduled after a certain
    amount of time (on victory).
    It's purpose is to simply go back to the main menu.
    """
    resources[EventWriter].push_event(CheckoutSceneCommand(CheckoutScene.MainMenu))

class IngameGUIPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(PlayersReadyCommand, on_players_ready_command)
        app.add_event_listener(ServerDisonnectedEvent, on_server_disconnection)

        app.add_event_listener(GameNotificationCommand, on_game_notification)