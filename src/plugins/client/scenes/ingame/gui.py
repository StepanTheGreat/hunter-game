from plugin import Plugin, Resources, EventWriter, resource_exists, run_if

from core.assets import AssetManager
from core.graphics import FontGPU, Texture, TextureAtlas
from core.time import SystemScheduler

from plugins.client.interfaces.gui_widgets import GUIElement, TextButton, Label, TextureRect
from plugins.client.services.playerstats import PlayerStats
from plugins.shared.services.network import Client, clean_network_actors

from plugins.client.commands import *
from plugins.client.events import *
from plugins.client.actions import ClientActionDispatcher, SignalPlayerReadyAction

from plugins.client.commands import PlayersReadyCommand, GameNotificationCommand, GameNotification

GO_BACK_TO_MENU_IN = 8
"The amount of time to wait during the victory stage to automatically go back"

POLICEMAN_WEAPON_SPEED = 15
ROBBER_WEAPON_SPEED = 20

class PlayerHealthbar(GUIElement):
    "A custom healthbar element for rendering the current player's health"

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

    def draw(self, renderer, dt: float):
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

class PlayerWeapon(GUIElement):
    "A GUI element for player weapon animations. It essentially simply plays animations and allows restarting them over"

    def __init__(
        self, 
        edge: tuple[int, int], 
        pivot: tuple[int, int], 
        size: tuple[int, int],
        sprites: tuple[Texture, ...],
        animation_speed: float
    ):
        super().__init__(edge, pivot)
        assert len(sprites) > 0, "No sprites were given to the weapon animator"

        self.sprites: tuple[Texture, ...] = sprites

        self.animation_speed = animation_speed
        self.animation_at = 0

        self.set_size(*size)

    def set_sprites(self, new_sprites: tuple[Texture, ...]):
        "Change the currently animated sequence of sprites"

        assert len(new_sprites) > 0, "Can't set an empty sequence of sprites"

        self.sprites = new_sprites

    def start_animation(self):
        "Restart the animation from the start"

        # Yep, we're cutting corners here
        self.animation_at = 0.001

    def draw(self, renderer, dt):

        # To really simplify the logic here... The animation logic runs only if the `animation_at`
        # attribute isn't 0. That means it's negative or positive. Doesn't matter.
        if self.animation_at != 0:

            # We're going to add to this counter our new delta time
            self.animation_at += dt * self.animation_speed

            # And now, if the current animation time is bigger than the amount of sprites we have - reset it
            # to zero, essentially stopping the animation entirely
            if self.animation_at > len(self.sprites):
                self.animation_at = 0

        # Of course render our animation at the current frame
        x, y, w, h = self.get_rect()
        renderer.draw_texture(
            self.sprites[int(self.animation_at)], 
            (x, y), 
            (w, h), 
            (255, 255, 255)
        )


class IngameGUI:
    "The GUI active during the actual game"

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
        self.player_weapon = PlayerWeapon(
            (1, 1), 
            (1, 1), 
            (256, 256), 
            self.assets.load(TextureAtlas, "images/sprites.atl").get_sprite_textures("gun_shot"),
            POLICEMAN_WEAPON_SPEED
        )
        self.players_ready_label = Label(self.font, "Players ready: 0/0", (0.5, 1), (0.5, 1), (255, 255, 255), 0.3)

        self.crosshair = TextureRect(
            self.assets.load(Texture, "images/sprites.atl#crosshair"),
            (32, 32),
            (0.5, 0.5),
            (0.5, 0.5)
        ).with_z(-1)

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
            self.player_weapon,
            self.quit_btn
        ]))

    def enter_game_stage(self):
        self.ewriter.push_event(ReplaceGUICommand([
            self.healthbar,
            self.quit_btn,
            self.player_weapon,
            self.crosshair
        ]))

    def enter_finish_stage(self, policemen_won: bool):

        text = "The policemen won!" if policemen_won else "The robster won!"
        color = (100, 100, 255) if policemen_won else (255, 100, 00)
        victory_label = Label(self.font, text, (0.5, 0.5), (0.5, 0.5), color, 0.4) 

        self.ewriter.push_event(ReplaceGUICommand([
            self.healthbar,
            self.crosshair,
            self.player_weapon,
            victory_label
        ]))

    def update_players_ready(self, ready: int, players: int):
        "Update the \"players ready\" label with new data from the server"

        self.players_ready_label.set_text(f"Players ready: {ready}/{players}")

    def restart_weapon_animation(self):
        "Start the weapon's animation all over again"

        self.player_weapon.start_animation()

    def enter_spectator_mode(self):
        "Disable most of player's GUI (healthbar, weapon and crosshair)"

        for element in (self.healthbar, self.player_weapon, self.crosshair):
            element.hide(True)

    def use_robber_weapon(self):
        "Switch this player's policeman's weapon to robber's"

        self.player_weapon.set_sprites(
            self.assets.load(TextureAtlas, "images/sprites.atl")
                .get_sprite_textures("knife_shot")
        )
        self.player_weapon.animation_speed = ROBBER_WEAPON_SPEED

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
    "When we receive a new players ready command, we would like to update our game label"

    gui = resources[IngameGUI]
    gui.update_players_ready(command.players_ready, command.players)

@run_if(resource_exists, IngameGUI)
def on_game_notification(resources: Resources, command: GameNotificationCommand):
    """
    This hook listens for game notifications and changes the UI based on the notification received.
    On game started, we would like to hide lobby GUI (like players ready and so on),
    and on victory we would like to change our current subscene to the victory one (with the victory
    label) and schedule our return home in a specific amount of time.
    """

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

@run_if(resource_exists, IngameGUI)
def on_player_weapon_use(resources: Resources, event: CharacterUsedWeaponEvent):
    "When the main player uses a weapon, we would like to play an animation"

    gui = resources[IngameGUI]
    
    if event.is_main:
        gui.restart_weapon_animation()

@run_if(resource_exists, IngameGUI)
def on_main_player_crook_revelation(resouces: Resources, _):
    "When our main player is a crook, we would like to change its weapon sprites to different ones"

    resouces[IngameGUI].use_robber_weapon()

@run_if(resource_exists, IngameGUI)
def on_main_player_death(resouces: Resources, _):
    "When our main player dies, we should enter the spectator mode and disable most GUIs"

    resouces[IngameGUI].enter_spectator_mode()

class IngameGUIPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(PlayersReadyCommand, on_players_ready_command)
        app.add_event_listener(ServerDisonnectedEvent, on_server_disconnection)

        app.add_event_listener(GameNotificationCommand, on_game_notification)
        app.add_event_listener(CharacterUsedWeaponEvent, on_player_weapon_use)

        app.add_event_listener(MainPlayerIsACrookEvent, on_main_player_crook_revelation)
        app.add_event_listener(MainPlayerDiedEvent, on_main_player_death)