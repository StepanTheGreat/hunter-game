from plugin import Resources, Plugin

from modules.scene import SceneBundle

from plugins.session import attach_listener, detach_listener

from .gui import MainMenuGUI, MainMenuGUIPlugin

class MainMenuScene(SceneBundle):
    def __init__(self, resources: Resources):
        super().__init__()
        self.add_auto_resources(MainMenuGUI(resources))

    def post_init(self, resources):
        # We're going to listen for server events right when we connect
        attach_listener(resources)

    def post_destroy(self, resources):
        # And of course, when we either quit the game or join a game - we close this listener
        detach_listener(resources)

class MainMenuPlugin(Plugin):
    def build(self, app):
        app.add_plugins(MainMenuGUIPlugin())