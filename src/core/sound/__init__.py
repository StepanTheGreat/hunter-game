from openal import *

oalInit()

from plugin import Plugin, Schedule, Resources

class SoundManager:
    def __init__(self):
        # A dummy implementation
        pass

def close_openal(resources: Resources):
    # Really important for gracefully quitting
    oalQuit()

class SoundPlugin(Plugin):
    def build(self, app):
        app.insert_resource(SoundManager())
        app.add_systems(Schedule.Finalize, close_openal)