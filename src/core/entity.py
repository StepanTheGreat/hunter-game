from plugin import Plugin, Resources, Schedule

from core.pg import Clock

from typing import Optional, TypeVar, Type

# Entity
E = TypeVar("E")

class Entity:
    "An entity is an object with custom update (per frame) and fixed update (frame independent) logic"    
    def update(self, dt: float, alpha: float):
        "Entity's custom update logic"
    
    def update_fixed(self, dt: float):
        "Entity's custom fixed update logic (usually for important behaviour)"
    
class EntityWorld:
    "A global storage of entities. It only manages storage and queries, not logic"
    def __init__(self):
        self.entities: dict[type, list[Entity]] = {}
        "A group based container. Entities here are grouped by their type, which is perfect for entity searches"

    def push_entity(self, entity: Entity):
        "Add a new entity to the entity container"
        ty = type(entity)

        if ty in self.entities:
            self.entities[ty].append(entity)
        else:
            self.entities[ty] = [entity]

    def remove_entity(self, entity: Entity):
        "Remove an entity by its reference"
        ty = type(entity)
        if ty in self.entities:
            ind = self.entities[ty].index(ind)
            if ind is not None:
                self.entities[ty].pop(ind)

    def get_group(self, ty: Type[E]) -> list[E]:
        return self.entities.get(ty, [])
    
    def update(self, dt: float, alpha: float):
        for group in self.entities.values():
            for entity in group:
                entity.update(dt, alpha)

    def update_fixed(self, dt: float):
        for group in self.entities.values():
            for entity in group:
                entity.update_fixed(dt)
    
    def clear(self):
        "Clear the entire world of all entities"
        self.entities.clear()

def update_entities(resources: Resources):
    entities = resources[EntityWorld]
    clock = resources[Clock]

    entities.update(clock.get_delta(), clock.get_alpha())

def update_fixed_entities(resources: Resources):
    entities = resources[EntityWorld]
    clock = resources[Clock]

    entities.update_fixed(clock.get_fixed_delta())
    
class EntityPlugin(Plugin):
    def build(self, app):
        app.insert_resource(EntityWorld())
        app.add_systems(Schedule.Update, update_entities)
        app.add_systems(Schedule.FixedUpdate, update_fixed_entities)