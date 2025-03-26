from plugin import Plugin

from typing import Optional, TypeVar, Type

ENTITY_UID_CAP = 2**16

# Entity
E = TypeVar("E")

class Entity:
    "An entity is simply an object container with an ID. Everything else is up to you"
    def __init__(self, uid: int):
        self.uid = uid
        "Entity's unique identifier across multiple sessions (not only a client variable)"

    def get_uid(self) -> int:
        return self.uid
    
class EntityWorld:
    "A global storage of entities. It only manages storage and queries, not logic"
    def __init__(self, entity_uid_cap: int = ENTITY_UID_CAP):
        assert entity_uid_cap > 0

        self.entity_uid_cap = entity_uid_cap
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
        self.entity_uid = self.entity_uid+1 % self.entity_uid_cap

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
                if entity.get_uid() == uid:
                    return entity

    def remove_entity(self, entity: Entity):
        "Remove an entity by its reference"
        ty = type(entity)
        if ty in self.entities:
            ind = self.entities[ty].index(ind)
            if ind is not None:
                self.entities[ty].pop(ind)

    def remove_entity_id(self, uid: int):
        """Remove an entity by its UID. This is a highly slow operation, since it will iterate EVERY group, and check EVERY entity"""
        for group in self.entities.values():
            for entity in group:
                if entity.get_uid() == uid:
                    group.remove(entity)
                    return

    def get_group(self, ty: Type[E]) -> list[E]:
        return self.entities.get(ty, [])
    
    def clear(self):
        "Clear the entire world of all entities and reset the entity UID counter"
        self.entity_uid = 0
        self.entities.clear()
    
class EntityPlugin(Plugin):
    def build(self, app):
        app.insert_resource(EntityWorld())