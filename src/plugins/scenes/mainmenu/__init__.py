import pygame as pg

from plugin import Resources, Plugin, Schedule, run_if, resource_exists

from core.assets import AssetManager

from modules.scene import SceneManager, SceneBundle

from plugins.graphics import Renderer2D, FontGPU

from ..ingame import IngameBundle

class MainMenu:
    def __init__(self, assets: AssetManager):
        self.font = assets.load(FontGPU, "fonts/font.ttf")

@run_if(resource_exists, MainMenu)
def draw_main_menu(resources: Resources):
    menu = resources[MainMenu]
    renderer = resources[Renderer2D]

    textw, texth = menu.font.measure("You're in main menu!")

    renderer.draw_rect((0, 0, 700, 700), (0.2, 0.2, 0.2))
    renderer.draw_text(menu.font, "You're in main menu!", (350-textw/2, 350-texth/2), (1, 1, 1), 1)

class MainMenuScene(SceneBundle):
    def __init__(self, resources: Resources):
        super().__init__(
            MainMenu(resources[AssetManager])
        )

class MainMenuPlugin(Plugin):
    def build(self, app):
        app.add_systems(Schedule.Render, draw_main_menu)