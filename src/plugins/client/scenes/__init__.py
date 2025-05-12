from plugin import Plugin, Schedule, EventWriter

from modules.scene import SceneManager

from plugins.client.commands import CheckoutSceneCommand, CheckoutScene

from .ingame import *
from .mainmenu import *

def on_checkout_scene_command(resources: Resources, command: CheckoutSceneCommand):
    """
    Because python REALLY doesn't like recursive imports, we will maintain a simple command listener to switch
    scenes manually.
    """
    scene_manager = resources[SceneManager]

    new_scene = command.new_scene
    if new_scene is CheckoutScene.InGame:
        scene_manager.insert_scene(IngameScene(resources))

    elif new_scene is CheckoutScene.MainMenu:
        scene_manager.insert_scene(MainMenuScene(resources))

def enter_default_scene_system(resources: Resources):
    # We will also initialize our scene manager with MainMenu being the default scene
    resources[EventWriter].push_event(CheckoutSceneCommand(CheckoutScene.MainMenu))    

class ScenesPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            IngamePlugin(),
            MainMenuPlugin()
        )
        app.insert_resource(SceneManager(app.get_resources()))

        app.add_systems(Schedule.Startup, enter_default_scene_system)
        app.add_event_listener(CheckoutSceneCommand, on_checkout_scene_command)