from plugin import *

from core import ServerCoreModulesPlugin
from plugins.shared import SharedPluginCollection

from modules.time import Clock

from app_config import CONFIG

from multiprocessing import Process, Value

class ServerController:
    def __init__(self):
        self.quit_val = Value("b", False)

    def make_quit(self):
        self.quit_val.value = True

    def should_quit(self) -> bool:
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
            print("SERVER: Updating!")
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
            ServerCoreModulesPlugin()
        )
        app.insert_resource(self.controller)
        app.insert_resource(Clock(CONFIG.fixed_fps, CONFIG.fixed_fps))
        app.set_runner(server_runner)

def make_and_run_server(controller: ServerController):
    app = App(
        AppBuilder(ServerPlugins(controller))
    )
    app.run()

class ServerHandle:
    def __init__(self):
        self.server_controller = ServerController()

        self.to_stop = 4

        self.process = Process(target=make_and_run_server, args=(self.server_controller,))

    def update(self, dt: float) -> bool:
        self.to_stop -= dt

        if self.to_stop < 0:
            self.stop_server()
            return False

        return True
    
    def start_server(self):
        print("Starting the server!")
        self.process.start()

    def stop_server(self):
        print("Stopping the server...")

        self.server_controller.make_quit()

        self.process.join()

        print("Have successfully stopped the server!")  

def kickstart_server(resources: Resources):
    resources[ServerHandle].start_server()

def update_server(resources: Resources):
    dt = resources[Clock].get_delta()

    if ServerHandle in resources:
        if not resources[ServerHandle].update(dt):
            resources.remove(ServerHandle)

class ServerManagementPlugin(Plugin):
    def build(self, app):
        app.insert_resource(ServerHandle())
        app.add_systems(Schedule.Startup, kickstart_server)
        app.add_systems(Schedule.Update, update_server)