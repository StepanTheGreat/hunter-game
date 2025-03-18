"An entity container plugin, resposible for managing game entities"

from plugin import Resources, Plugin
from clock import Clock

class Entity:
    def __init__(self):
        self.alive: bool = False

    def is_alive(self) -> bool:
        "Check whether this entity is alive or not. Dead entities will be removed by the Entity Manager"
        return self.alive
    
    def update(self, resources: Resources, dt: float):
        "Entity's update logic"

class EntityContainer:
    def __init__(self):
        self.entities: list[Entity] = []

    def push_entity(self, entity: Entity):
        self.entities.append(entity)

    def update(self, resources: Resources):
        dt = resources[Clock].get_delta()

        # A deletion index stack
        to_delete = []
        for ind, entity in enumerate(self.entities):
            entity.update(resources, dt)
            if not entity.is_alive():
                to_delete.append(ind)

        while to_delete:
            self.entities.pop(to_delete.pop())