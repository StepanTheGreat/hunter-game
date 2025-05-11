from plugin import *

from .runner import run_server_process, ServerController

class ServerExecutor:
    def __init__(self):
        self.server_controller = ServerController()
        self.server_process = None
    
    def start_server(self) -> tuple[str, int]:
        "Start a new server process (if not already present) and return its address"
        
        assert self.server_process is None, "The server is still running, can't start another one"

        print("Starting the server!")
        self.server_process, addr = run_server_process(self.server_controller)

        return addr

    def stop_server(self):
        assert self.server_process is not None, "The server isn't running, can't stop"

        print("Stopping the server...")

        self.server_controller.make_quit()

        self.server_process.join()
        self.server_controller.reset()

        self.server_process = None

        print("Have successfully stopped the server!")  

    def is_running(self) -> bool:
        "Is the server process running?"

        return self.server_process is not None

def quit_close_server(resources: Resources):
    "When quitting the app, it's important to first close the server"

    executor = resources[ServerExecutor]

    if executor.is_running():
        executor.stop_server()

class ServerManagementPlugin(Plugin):
    def build(self, app):
        app.insert_resource(ServerExecutor())
        app.add_systems(Schedule.Finalize, quit_close_server)
