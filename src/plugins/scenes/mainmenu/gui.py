from plugin import Resources

from core.assets import AssetManager

from modules.scene import SceneManager

from plugins.graphics import FontGPU
from plugins.gui import GUIBundleManager, TextButton, ColorRect, Label

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

        def insert_ingame_scene(as_server: bool):
            self.resources[SceneManager].insert_scene(IngameScene(self.resources, as_server))
        
        join_btn = (TextButton(font, "Join Game", (0.5, 0.5), MainMenuGUI.BUTTON_SIZE, text_scale=0.5)
            #.as_immediate(False)
            .with_callback(lambda: insert_ingame_scene(False)))
        
        create_btn = (TextButton(font, "Create Game", (0, 1), MainMenuGUI.BUTTON_SIZE, text_scale=0.5)
            .with_callback(lambda: insert_ingame_scene(True))
            .with_margin(0, 4)
            .attached_to(join_btn))

        def go_to_settings():
            self.enter_settings_subscene()

        settings_btn = (TextButton(font, "Settings", (0, 1), MainMenuGUI.BUTTON_SIZE, text_scale=0.5)
            .with_margin(0, 4)
            .with_callback(go_to_settings)
            .attached_to(create_btn))
        
        *_, tree_w, tree_h =  join_btn.measure_tree()
        join_btn.set_margin(-tree_w/2, -tree_h/2)

        self.gui.replace_gui([
            background, join_btn, 
        ])

    def enter_settings_subscene(self):
        font = self.assets.load(FontGPU, "fonts/font.ttf")

        background = ColorRect((100, 100, 100))

        def go_back():
            self.enter_mainmenu_subscene()

        back_btn = (TextButton(font, "<<", (0, 0), (64, 64))
            .with_callback(go_back))

        resolution_label = Label(font, "Resolution: ", (0.5, 0.5), text_scale=0.5)
        keys_label = Label(font, "Keys: ", (0, 1), text_scale=0.5).attached_to(resolution_label)
        vsync = Label(font, "Vsync: ", (0, 1), text_scale=0.5).attached_to(keys_label)

        *_, tree_w, tree_h =  resolution_label.measure_tree()
        resolution_label.set_margin(-tree_w/2, -tree_h/2)
        
        self.gui.replace_gui([
            background, back_btn, resolution_label, 
        ])