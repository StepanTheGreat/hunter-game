from plugin import Schedule, Plugin, Resources

from states import AppState, SceneState

class ScenesPlugin(Plugin):
    def build(self, app):
        app.insert_resource(AppState(SceneState.MainMenu))