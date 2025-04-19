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

        background = ColorRect((0, 0, 1))

        def start_game():
            self.resources[SceneManager].insert_scene(IngameScene(self.resources))

        play_btn = (TextButton(font, "Play", (0.5, 0.5), MainMenuGUI.BUTTON_SIZE, text_scale=2)
            .with_callback(start_game))

        def go_to_settings():
            self.enter_settings_subscene()

        settings_btn = (TextButton(font, "Settings", (0, 1), MainMenuGUI.BUTTON_SIZE, text_scale=2)
            .with_margin(0, 4)
            .with_callback(go_to_settings)
            .attached_to(play_btn))
        
        *_, tree_w, tree_h =  play_btn.measure_tree()
        play_btn.set_margin(-tree_w/2, -tree_h/2)

        self.gui.replace_gui([
            background, play_btn, 
        ])

    def enter_settings_subscene(self):
        font = self.assets.load(FontGPU, "fonts/font.ttf")

        background = ColorRect((0.4, 0.4, 0.4))

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