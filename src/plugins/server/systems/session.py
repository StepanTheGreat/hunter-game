from plugin import Plugin, Schedule, Resources

from ..actions import SyncTimeAction, ServerActionDispatcher

from core.time import Clock, schedule_systems_seconds

def tick_sync_client_timer_system(resources: Resources):
    "This system runs in a while and essentially syncronizes client's clock with the server's"

    dispatcher = resources[ServerActionDispatcher]
    clock = resources[Clock]
    
    # Once in a while, we're going to syncronize client's clock with ours
    dispatcher.dispatch_action(SyncTimeAction(clock.get_execution_time()))    

class SessionSystemsPlugin(Plugin):
    def build(self, app):
        # In this plugin we're going to initialize the game session resource and the server
        schedule_systems_seconds(
            app,
            (tick_sync_client_timer_system, 5, True)
        )