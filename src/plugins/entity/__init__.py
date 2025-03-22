from plugin import Resources, Plugin, Schedule

from modules.entity import EntityContainer

from .player import PlayerPlugin

def update_entities(resources: Resources):
    resources[EntityContainer].update(resources)

def draw_entities(resources: Resources):
    resources[EntityContainer].draw(resources)

class EntityPlugin(Plugin):
    "A general entity manager and executor. All game entities are stored and executed here"
    def build(self, app):
        app.insert_resource(EntityContainer())
        app.add_systems(Schedule.Update, update_entities)
        app.add_systems(Schedule.Render, draw_entities)
        app.add_plugins(PlayerPlugin())