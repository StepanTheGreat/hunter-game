from plugin import Resources
from typing import Optional
from core.pg import Clock

ENTITY_UID_CAP = 2**16

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

        self.entities: list[Entity] = []

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
        self.entities.append(entity)

    def get_entity(self, uid: int) -> Optional[Entity]:
        "Linearly search the entire entity array for an entity with the provided UID"

        for entity in self.entities:
            if entity.uid == uid:
                return entity

    def update(self, resources: Resources):
        "Call update logic for every entity"

        dt = resources[Clock].get_delta()

        to_remove = []
        for ind, entity in enumerate(self.entities):
            entity.update(resources, dt)

            if not entity.is_alive():
                to_remove.append(ind)

        # If there are entities to remove, we will pop them from the stack
        # and gradually remove. This is a slow operation however
        while to_remove:
            self.entities.pop(to_remove.pop())
    
    def draw(self, resources: Resources):
        "Call rendering logic for every entity"

        for entity in self.entities:
            entity.draw(resources)