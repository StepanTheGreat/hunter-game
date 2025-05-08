from plugin import Resources, Plugin

from modules.scene import SceneBundle

from plugins.shared.services.network import BroadcastListener, insert_network_actor, clean_network_actors
from plugins.rpcs.listener import LISTENER_PORT, LISTENER_RPCS

from .gui import MainMenuGUI, MainMenuGUIPlugin

class MainMenuScene(SceneBundle):
    def __init__(self, resources: Resources):
        super().__init__()
        self.add_auto_resources(
            MainMenuGUI(resources),
        )

    def post_init(self, resources):
        # We're going to listen for server events right when we connect
        # attach_listener(resources)
        insert_network_actor(resources, BroadcastListener(resources, LISTENER_PORT, LISTENER_RPCS))

    def post_destroy(self, resources):
        # And of course, when we either quit the game or join a game - we close this listener
        # detach_listener(resources)
        clean_network_actors(resources, BroadcastListener)

class MainMenuPlugin(Plugin):
    def build(self, app):
        app.add_plugins(MainMenuGUIPlugin())