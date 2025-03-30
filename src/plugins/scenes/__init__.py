from plugin import Plugin

from modules.scene import SceneManager

from .ingame import IngamePlugin
from .mainmenu import MainMenuPlugin, MainMenuScene

class ScenesPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            IngamePlugin(),
            MainMenuPlugin()
        )
        # We will also initialize our scene manager with MainMenu being the default scene
        app.insert_resource(SceneManager(
            app.get_resources(),
            MainMenuScene(app.get_resources())
        ))