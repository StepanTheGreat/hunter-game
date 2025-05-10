from plugin import *

from core import ServerCoreModulesPlugin

from core.time import Clock

from plugins.shared.services.network import Server
from plugins.shared import SharedPluginsCollection

from .actions import ServerActionPlugin
from .systems import ServerSystemsPlugin
from .handlers import ServerHandlersPlugin
from .services import ServerServicesPlugin

from app_config import CONFIG

from multiprocessing import Process, Value, Queue

class ServerController:
    """
    The class that gets passed to the server process to control when to stop its execution.
    Essentially, this is a boolean value, that server checks every frame. When it is set to `True`
    (should stop) - it's going to finish everything and stop the process.
    """
    def __init__(self):
        self.quit_val = Value("b", False)
        "This is an inter-process value which tells the player when to stop"

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
    ewriter = app.get_resource(EventWriter)

    caught_exception = None

    print("SERVER: Starting!")
    app.startup()

    try:
        while not server_controller.should_quit():
            clock.update()
            app.update(clock.get_fixed_updates())            
    except Exception as exception:

        # We don't want to handle events when an app has caught an exception - only finalize it
        ewriter.clear_events()
        
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
            ServerCoreModulesPlugin(),
            SharedPluginsCollection(),
            ServerServicesPlugin(),
            ServerSystemsPlugin(),
            ServerActionPlugin(),
            ServerHandlersPlugin(),
        )
        app.insert_resource(self.controller)
        app.insert_resource(Clock(CONFIG.fixed_fps, CONFIG.fixed_fps))
        app.set_runner(server_runner)

def _run_server_process(controller: ServerController, addr_queue: Queue):
    app = App(
        AppBuilder(ServerPlugins(controller))
    )

    # This is a really simple workaround, but we will send the server's address via this
    # queue
    addr_queue.put(app.get_resource(Server).get_addr())

    app.run()

def run_server_process(controller: ServerController) -> tuple[Process, tuple[str, int]]:
    """
    Create a separate server process, start it, and return its process handle with the server's 
    address. This process will block
    """
    addr_queue = Queue(1)

    # Start our server on a separate process. We'll pass it our controller and address queue
    process = Process(target=_run_server_process, args=(controller, addr_queue))
    process.start()

    # Now we're going to get our address back and close the queue
    server_addr = addr_queue.get(True)
    addr_queue.close()

    # Return both the process and our server's address
    return process, server_addr