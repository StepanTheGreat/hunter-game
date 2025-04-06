import pygame as pg

from plugin import Resources, Plugin, Schedule, run_if, resource_exists

from core.assets import AssetManager
from core.pg import Screen

from modules.scene import SceneManager, SceneBundle

from plugins.graphics import Renderer2D, FontGPU
from plugins.gui import GUIManager, TextButton, ColorRect, GUIElement, Label

from ..ingame import IngameScene

class MainMenu:
    BUTTON_SIZE = (312, 64)

    class SubScene:
        MainMenu = 0,
        Settings = 1

    def __init__(self, resources: Resources):
        self.resources = resources
        self.gui = resources[GUIManager]
        self.screen = resources[Screen]
        self.assets = resources[AssetManager]

        self.gui_elements = []
        self.sub_scene = MainMenu.SubScene.MainMenu

        self.enter_subscene(self.sub_scene)

    def mainmenu_subscene(self):
        screen_w, screen_h = self.screen.get_size()
        font = self.assets.load(FontGPU, "fonts/font.ttf")

        background = ColorRect((0, 0), (0, 0), (screen_w, screen_h), (0, 0, 1))

        def start_game():
            self.resources[SceneManager].insert_scene(IngameScene(self.resources))

        play_btn = (TextButton(font, "Play", (0, 0), MainMenu.BUTTON_SIZE, text_scale=2)
            .with_callback(start_game))

        def go_to_settings():
            self.enter_subscene(MainMenu.SubScene.Settings)

        settings_btn = (TextButton(font, "Settings", (0, 1), MainMenu.BUTTON_SIZE, text_scale=2)
            .with_margin(0, 4)
            .with_callback(go_to_settings)
            .attached_to(play_btn))
        
        play_btn.set_tree_position(screen_w/2, screen_h/2, (0.5, 0.5))
        
        self.insert_subscene_gui([
            background, play_btn, 
        ])

    def settings_subscene(self):
        screen_w, screen_h = self.screen.get_size()
        font = self.assets.load(FontGPU, "fonts/font.ttf")

        background = ColorRect((0, 0), (0, 0), (screen_w, screen_h), (0.4, 0.4, 0.4))

        def go_back():
            self.enter_subscene(MainMenu.SubScene.MainMenu)

        back_btn = (TextButton(font, "<<", (0, 0), (64, 64))
            .with_callback(go_back))

        resolution_label = Label(font, "Resolution: ", (0, 0), text_scale=0.5)
        keys_label = Label(font, "Keys: ", (0, 1), text_scale=0.5).attached_to(resolution_label)
        vsync = Label(font, "Vsync: ", (0, 1), text_scale=0.5).attached_to(keys_label)

        resolution_label.set_tree_position(screen_w/2, screen_h/2, (0.5, 0.5))
        
        self.insert_subscene_gui([
            background, back_btn, resolution_label, 
        ])
    
    def enter_subscene(self, subscene_id: int):
        if subscene_id == MainMenu.SubScene.MainMenu:
            self.mainmenu_subscene()
        elif subscene_id == MainMenu.SubScene.Settings:
            self.settings_subscene()    
    
    def insert_subscene_gui(self, new_elements: list[GUIElement]):
        if self.gui_elements is not None:
            self.gui.remove_elements(*self.gui_elements)

        self.gui.add_elements(*new_elements)
        self.gui_elements = new_elements

    def cleanup(self):
        self.gui.remove_elements(*self.gui_elements)

class MainMenuScene(SceneBundle):
    def __init__(self, resources: Resources):
        super().__init__(MainMenu(resources))

    def destroy(self, resources):
        resources[MainMenu].cleanup()

class MainMenuPlugin(Plugin):
    def build(self, app):
        pass