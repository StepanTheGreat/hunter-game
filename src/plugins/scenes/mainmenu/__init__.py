from plugin import Resources, Plugin

from modules.scene import SceneBundle

from .gui import MainMenuGUI

class MainMenuScene(SceneBundle):
    def __init__(self, resources: Resources):
        super().__init__()
        self.add_auto_resources(MainMenuGUI(resources))

class MainMenuPlugin(Plugin):
    def build(self, app):
        pass