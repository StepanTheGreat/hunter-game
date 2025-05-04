from plugin import *

from core import ServerCoreModulesPlugin
from plugins.shared import SharedPluginCollection
from .uid import UIDManagerPlugin

from modules.time import Clock

from app_config import CONFIG

from multiprocessing import Process, Value

class ServerController:
    """
    The class that gets passed to the server process to control when to stop its execution.
    Essentially, this is a boolean value, that server checks every frame. When it is set to `True`
    (should stop) - it's going to finish everything and stop the process.
    """
    def __init__(self):
        self.quit_val = Value("b", False)

    def make_quit(self):
        "Signal the server to terminate"

        self.quit_val.value = True

    def reset(self):
        "Reset this server controller for the next server process"

        self.quit_val.value = False

    def should_quit(self) -> bool:
        "Should the server process with this controller quit? Used by the server runner"

        return self.quit_val.value == True

def server_runner(app: App):
    "A really simple server runner"

    clock = app.get_resource(Clock)
    server_controller = app.get_resource(ServerController)

    caught_exception = None

    print("SERVER: Starting!")
    app.startup()

    try:
        while not server_controller.should_quit():
            clock.update()
            app.update(clock.get_fixed_updates())            
    except Exception as exception:
        caught_exception = exception
        print("The server app has caught an exception, finalizing...")

    app.finalize()
    print("SERVER: Finalizing!")

    if caught_exception is not None:
        raise caught_exception

class ServerPlugins(Plugin):
    "The plugin collection that the server uses"
    def __init__(self, controller: ServerController):
        self.controller = controller

    def build(self, app):
        app.add_plugins(
            SharedPluginCollection(),
            ServerCoreModulesPlugin(),
            UIDManagerPlugin()
        )
        app.insert_resource(self.controller)
        app.insert_resource(Clock(CONFIG.fixed_fps, CONFIG.fixed_fps))
        app.set_runner(server_runner)

def _run_server(controller: ServerController):
    app = App(
        AppBuilder(ServerPlugins(controller))
    )
    app.run()

def run_server(controller: ServerController) -> Process:
    """
    Create a separate server process, start it, and return its process handle
    """
    process = Process(target=_run_server, args=(controller,))
    process.start()
    return process