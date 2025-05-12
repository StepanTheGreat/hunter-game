from plugin import Plugin, Resources, EventWriter

from core.assets import AssetManager

from modules.scene import SceneBundle

from plugins.client.commands import *
from plugins.shared.services.map import WorldMap
from plugins.shared.services.network import clean_network_actors, Client

from plugins.server import ServerExecutor

from plugins.client.services.session import ServerTime

from .gui import *

class IngameScene(SceneBundle):
    "The ingame scene"

    def __init__(self, resources: Resources):
        super().__init__()

        self.add_auto_resources(
            IngameGUI(resources)
        )

    def pre_init(self, resources):
        # Before we're going to load this scene, we will load our world map first
        assets = resources[AssetManager]

        wmap = assets.load(WorldMap, "maps/map1.json")
        resources[EventWriter].push_event(LoadMapCommand(wmap))
        resources[EventWriter].push_event(ResetSceneLightsCommand())

    def post_init(self, resources):
        # We're going to start the clock when the scene starts
        resources[ServerTime].start()
        
    def post_destroy(self, resources):
        resources[EventWriter].push_event(UnloadMapCommand())

        # We need to close our client before leaving
        clean_network_actors(resources, Client)

        # If we're running a server - we're going to stop it as well
        server_executor = resources[ServerExecutor]
        if server_executor.is_running():
            server_executor.stop_server()

        # This is highly important, as reusing the same UID manager will lead to instabilities
        resources[EventWriter].push_event(ResetEntityUIDManagerCommand())

        # And now we can safely remove all existing entities
        resources[EventWriter].push_event(CleanUpEntitiesCommand())

        # Reset and stop our server time
        resources[ServerTime].stop_and_reset()

class IngamePlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            IngameGUIPlugin()
        )