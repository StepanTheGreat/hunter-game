from plugin import Resources, Plugin, EventWriter, run_if, resource_exists

from core.assets import AssetManager

from plugins.client.services.graphics import FontGPU
from plugins.client.interfaces.gui_widgets import TextButton, ColorRect, Label

from plugins.shared.services.network import Client, insert_network_actor

from plugins.client.events import ServerConnectedEvent
from plugins.client.commands import ClearGUICommand, ReplaceGUICommand, CheckoutScene, CheckoutSceneCommand

from plugins.rpcs.client import CLIENT_RPCS

from plugins.rpcs.listener import AvailableServerCommand

from plugins.server import ServerExecutor

class MainMenuGUI:
    BUTTON_SIZE = (312, 64)

    def __init__(self, resources: Resources):
        self.resources = resources
        self.ewriter = resources[EventWriter]
        self.assets = resources[AssetManager]

        self.ewriter.push_event(ClearGUICommand())
        self.enter_mainmenu_subscene()

    def enter_mainmenu_subscene(self):
        font = self.assets.load(FontGPU, "fonts/font.ttf")

        background = ColorRect((0, 0, 255))

        # def insert_ingame_scene(as_server: bool):
            # self.resources[SceneManager].insert_scene(IngameScene(self.resources, as_server))

        def start_game_session(as_server: bool):
            if as_server:
                new_client = Client(self.resources, CLIENT_RPCS)
                addr = self.resources[ServerExecutor].start_server()
                new_client.try_connect(addr)
                insert_network_actor(self.resources, new_client)            

        create_btn = (TextButton(font, "Create Game", (0.5, 0.5), MainMenuGUI.BUTTON_SIZE, text_scale=0.5)
            .with_callback(lambda: start_game_session(True))
            )

        def go_to_settings():
            self.enter_settings_subscene()

        settings_btn = (TextButton(font, "Settings", (0, 1), MainMenuGUI.BUTTON_SIZE, text_scale=0.5)
            .with_margin(0, 10)
            .with_callback(go_to_settings)
            .attached_to(create_btn))
        
        def quit_game():
            exit()

        quit_btn = (TextButton(font, "Quit", (0, 1), MainMenuGUI.BUTTON_SIZE, text_scale=0.5)
            .with_margin(0, 10)
            .with_callback(quit_game)
            .attached_to(settings_btn))
        
        # These 2 lines will measure the tree, and using margin try to align them
        *_, tree_w, tree_h =  create_btn.measure_tree()
        create_btn.set_margin(-tree_w/2, -tree_h/2)

        self.ewriter.push_event(ReplaceGUICommand([background, create_btn]))

    def enter_settings_subscene(self):
        font = self.assets.load(FontGPU, "fonts/font.ttf")

        background = ColorRect((100, 100, 100))

        def go_back():
            self.enter_mainmenu_subscene()

        back_btn = (TextButton(font, "<<", (0, 0), (64, 64))
            .attached_to(background)
            .with_callback(go_back))

        resolution_label = Label(font, "Resolution: ", (0.5, 0.5), text_scale=0.5).attached_to(background)
        keys_label = Label(font, "Keys: ", (0, 1), text_scale=0.5).attached_to(resolution_label)
        vsync = Label(font, "Vsync: ", (0, 1), text_scale=0.5).attached_to(keys_label)

        *_, tree_w, tree_h =  resolution_label.measure_tree()
        resolution_label.set_margin(-tree_w/2, -tree_h/2)
        
        self.ewriter.push_event(ReplaceGUICommand([background]))

@run_if(resource_exists, MainMenuGUI)
def on_connection_accepted(resources: Resources, _: ServerConnectedEvent):
    resources[EventWriter].push_event(CheckoutSceneCommand(CheckoutScene.InGame))

def on_available_server(resources: Resources, command: AvailableServerCommand):
    new_client = Client(resources, CLIENT_RPCS)
    new_client.try_connect(command.addr)
    insert_network_actor(resources, new_client)

class MainMenuGUIPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(ServerConnectedEvent, on_connection_accepted)

        app.add_event_listener(AvailableServerCommand, on_available_server)