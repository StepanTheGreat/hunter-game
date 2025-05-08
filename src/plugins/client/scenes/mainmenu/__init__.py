from plugin import Resources, Plugin

from modules.scene import SceneBundle

<<<<<<< HEAD
from plugins.shared.network import Listener, insert_network_actor, clean_network_actors
=======
from plugins.shared.network import BroadcastListener, insert_network_actor, clean_network_actors
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
from plugins.rpcs.listener import LISTENER_PORT, LISTENER_RPCS
from plugins.shared.components import reset_entity_uid_manager

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
<<<<<<< HEAD
        insert_network_actor(resources, Listener(resources, LISTENER_PORT, LISTENER_RPCS))
=======
        insert_network_actor(resources, BroadcastListener(resources, LISTENER_PORT, LISTENER_RPCS))
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75

    def post_destroy(self, resources):
        # And of course, when we either quit the game or join a game - we close this listener
        # detach_listener(resources)
<<<<<<< HEAD
        clean_network_actors(resources, Listener)
=======
        clean_network_actors(resources, BroadcastListener)
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75

class MainMenuPlugin(Plugin):
    def build(self, app):
        app.add_plugins(MainMenuGUIPlugin())