from plugin import Resources, Plugin

from core.assets import AssetManager

from modules.scene import SceneManager

from plugins.client.services.graphics import FontGPU
from plugins.client.services.gui import GUIBundleManager, TextButton, ColorRect, Label

from plugins.shared.services.network import Client, insert_network_actor

from plugins.client.events import ServerConnectedEvent

from plugins.rpcs.client import CLIENT_RPCS

from plugins.server import ServerExecutor

from ..ingame import IngameScene

class MainMenuGUI:
    BUTTON_SIZE = (312, 64)

    def __init__(self, resources: Resources):
        self.resources = resources
        self.gui = resources[GUIBundleManager]
        self.assets = resources[AssetManager]

        self.gui.clear()
        self.enter_mainmenu_subscene()

    def enter_mainmenu_subscene(self):
        font = self.assets.load(FontGPU, "fonts/font.ttf")

        background = ColorRect((0, 0, 255))

        # def insert_ingame_scene(as_server: bool):
            # self.resources[SceneManager].insert_scene(IngameScene(self.resources, as_server))

        def start_game_session(as_server: bool):
            # self.resources[SceneManager].insert_scene(IngameScene(self.resources))
            # return
            new_client = Client(self.resources, CLIENT_RPCS)
            if as_server:
                print("Pressed as the server")
                addr = self.resources[ServerExecutor].start_server()
            else:
                print("Pressed as a client")
                addr = input("Address: ")
                ip, port = addr.split(":")
                addr = (ip, int(port))

            new_client.try_connect(addr)
            insert_network_actor(self.resources, new_client)

        join_btn = (TextButton(font, "Join Game", (0.5, 0.5), MainMenuGUI.BUTTON_SIZE, text_scale=0.5)
            .attached_to(background)
            .with_callback(lambda: start_game_session(False)))
        
        create_btn = (TextButton(font, "Create Game", (0, 1), MainMenuGUI.BUTTON_SIZE, text_scale=0.5)
            .with_callback(lambda: start_game_session(True))
            .with_margin(0, 4)
            .attached_to(join_btn))

        def go_to_settings():
            self.enter_settings_subscene()

        settings_btn = (TextButton(font, "Settings", (0, 1), MainMenuGUI.BUTTON_SIZE, text_scale=0.5)
            .with_margin(0, 4)
            .with_callback(go_to_settings)
            .attached_to(create_btn))
        
        # These 2 lines will measure the tree, and using margin try to align them
        *_, tree_w, tree_h =  join_btn.measure_tree()
        join_btn.set_margin(-tree_w/2, -tree_h/2)

        self.gui.replace_gui([background])

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
        
        self.gui.replace_gui([background])

def on_connection_accepted(resources: Resources, event: ServerConnectedEvent):
    if MainMenuGUI in resources:
        resources[SceneManager].insert_scene(IngameScene(resources))

class MainMenuGUIPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(ServerConnectedEvent, on_connection_accepted)