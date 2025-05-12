from plugin import Resources, Plugin, EventWriter, run_if, resource_exists

from core.assets import AssetManager
from core.events import QuitEvent

from plugins.client.services.graphics import FontGPU
from plugins.client.interfaces.gui_widgets import TextButton, ColorRect, Label

from plugins.shared.services.network import Client, insert_network_actor

from plugins.client.events import ServerConnectedEvent
from plugins.client.commands import ClearGUICommand, ReplaceGUICommand, CheckoutScene, CheckoutSceneCommand

from plugins.rpcs.client import CLIENT_RPCS

from plugins.rpcs.listener import AvailableServerCommand

from plugins.server import ServerExecutor

class MainMenuGUI:
    "Our main game GUI"

    BUTTON_SIZE = (312, 64)

    def __init__(self, resources: Resources):
        self.resources = resources
        self.ewriter = resources[EventWriter]
        self.assets = resources[AssetManager]

        self.ewriter.push_event(ClearGUICommand())
        self.enter_mainmenu_subscene()

    def enter_mainmenu_subscene(self):
        font = self.assets.load(FontGPU, "fonts/font.ttf")

        game_title_label = Label(
            font,
            "Hunter Game",
            (0.5, 0),
            (0.5, 0),
            (255, 200, 50),
            0.5
        ).with_margin(0, 10)

        music_credits_label = Label(
            font, 
            "Music made by Karl Casey @ White Bat Audio", 
            (0, 1), 
            (0, 1), 
            (255, 255, 255), 
            0.3
        )

        def start_game_session():
            new_client = Client(self.resources, CLIENT_RPCS)
            addr = self.resources[ServerExecutor].start_server()
            new_client.try_connect(addr)
            insert_network_actor(self.resources, new_client)            

        create_btn = (TextButton(font, "Create Game", (0.5, 0.5), MainMenuGUI.BUTTON_SIZE, text_scale=0.5)
            .with_callback(start_game_session)
            )

        def go_to_settings():
            self.enter_settings_subscene()

        settings_btn = (TextButton(font, "Settings", (0, 1), MainMenuGUI.BUTTON_SIZE, text_scale=0.5)
            .with_margin(0, 10)
            .with_callback(go_to_settings)
            .attached_to(create_btn))
        
        def quit_game():
            self.ewriter.push_event(QuitEvent(None))

        quit_btn = (TextButton(font, "Quit", (0, 1), MainMenuGUI.BUTTON_SIZE, text_scale=0.5)
            .with_margin(0, 10)
            .with_callback(quit_game)
            .attached_to(settings_btn))
        
        # These 2 lines will measure the tree, and using margin try to align them
        *_, tree_w, tree_h =  create_btn.measure_tree()
        create_btn.set_margin(-tree_w/2, -tree_h/2)

        self.ewriter.push_event(ReplaceGUICommand([
            game_title_label,
            music_credits_label,
            create_btn
        ]))

    def enter_settings_subscene(self):
        font = self.assets.load(FontGPU, "fonts/font.ttf")

        def go_back():
            self.enter_mainmenu_subscene()

        back_btn = (TextButton(font, "<<", (0, 0), (64, 64))
            .with_callback(go_back))

        resolution_label = Label(font, "Resolution: ", (0.5, 0.5), text_scale=0.5)
        keys_label = Label(font, "Keys: ", (0, 1), text_scale=0.5).attached_to(resolution_label)
        vsync = Label(font, "Vsync: ", (0, 1), text_scale=0.5).attached_to(keys_label)

        *_, tree_w, tree_h =  resolution_label.measure_tree()
        resolution_label.set_margin(-tree_w/2, -tree_h/2)
        
        self.ewriter.push_event(ReplaceGUICommand([back_btn, resolution_label]))

@run_if(resource_exists, MainMenuGUI)
def on_connection_accepted(resources: Resources, _: ServerConnectedEvent):
    "When a connection is accepted by the server - we would like to switch the current scene and load the game"

    resources[EventWriter].push_event(CheckoutSceneCommand(CheckoutScene.InGame))

def on_available_server(resources: Resources, command: AvailableServerCommand):
    "The currently lazy approach is to simply automatically connect to any available server this client sees."

    new_client = Client(resources, CLIENT_RPCS)
    new_client.try_connect(command.addr)
    insert_network_actor(resources, new_client)

class MainMenuGUIPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(ServerConnectedEvent, on_connection_accepted)

        app.add_event_listener(AvailableServerCommand, on_available_server)