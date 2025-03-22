from plugin import Resources
from typing import Optional, TypeVar, Type
from core.pg import Clock

ENTITY_UID_CAP = 2**16

# Entity
E = TypeVar("E")

class Entity:
    def __init__(self, uid: int):
        self.uid = uid
        self.alive = True
        "Entity's unique identifier across multiple sessions (not only a client variable)"
    
    def update(self, resources: Resources, dt: float):
        "Entity's internal logic"

    def draw(self, resources: Resources):
        "Entity's rendering logic"

    def kill(self):
        "Queue an entity removal for this entity"
        self.alive = False

    def is_alive(self) -> bool:
        "Should this entity be removed?"
        return self.alive

class EntityContainer:
    def __init__(self):
        self.entity_uid = 0
        "An automatically incremented entity ID"

        self.entities: dict[type, list[Entity]] = {}
        "A group based container. Entities here are grouped by their type, which is perfect for entity searches"

    def get_entity_uid(self) -> int:
        """
        Get a new unique entity unique identifier. If reached the entity cap - will start from zero.
        
        ## Attention
        This will increment the internal entity counter, so don't waste the UID you get.
        """

        uid = self.entity_uid

        # Automatically reset the UID counter to 0 when the cap is reached.
        # This is not really possible in normal circumstances, but I guess it's good to have? 
        self.entity_uid = self.entity_uid+1 % ENTITY_UID_CAP

        return uid

    def push_entity(self, entity: Entity):
        "Add a new entity to the entity container"
        ty = type(entity)

        if ty in self.entities:
            self.entities[ty].append(entity)
        else:
            self.entities[ty] = [entity]

    def get_entity(self, uid: int) -> Optional[Entity]:
        "Linearly search the all entity groups for an entity with the provided UID"

        for entity_group in self.entities.values():
            for entity in entity_group:
                if entity.uid == uid:
                    return entity

    def update(self, resources: Resources):
        "Call update logic for every entity"

        dt = resources[Clock].get_delta()

        for entity_group in self.entities.values():
            to_remove = []
            for ind, entity in enumerate(entity_group):
                entity.update(resources, dt)

                if not entity.is_alive():
                    to_remove.append(ind)

            # If there are entities to remove, we will pop them from the stack
            # and gradually remove. This is a slow operation however
            while to_remove:
                entity_group.pop(to_remove.pop())
    
    def draw(self, resources: Resources):
        "Call rendering logic for every entity"

        for entity_group in self.entities.values():
            for entity in entity_group:
                entity.draw(resources)

    def get_group(self, ty: Type[E]) -> list[E]:
        return self.entities.get(ty, [])