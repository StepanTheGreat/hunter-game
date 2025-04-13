"A really minimal ECS module mostly inspired by [esper](https://github.com/benmoran56/esper)"

from typing import TypeVar, Type, Any, overload, Iterable
from itertools import count

# Yup, that's neccessary for adequate typing
C = TypeVar("C")
C2 = TypeVar("C2")
C3 = TypeVar("C3")
C4 = TypeVar("C4")

class WorldECS:
    """
    An entity container for all your ECS operations. You can learn about ECS [here](https://github.com/SanderMertens/ecs-faq?tab=readme-ov-file#what-is-ecs)
    
    This is the most primitive version of ECS, thus it doesn't even feature caching (currently). If performance becomes a bottleneck (it will pretty soon) - 
    one will be implemented here.
    """
    def __init__(self):
        self.components_to_entity: dict[type, set[int]] = {}
        "A component to entity map used when querying entities based on their components"

        self.entities: dict[int, dict[Type[Any], Any]] = {}
        "The actual entity ID to component storage."

        self.__entity_counter = count(start=0)

    def __add_components_to_entity_entry(self, component: Type, entity: int):
        if component in self.components_to_entity:
            self.components_to_entity[component].add(entity)
        else:
            self.components_to_entity[component] = {entity}

    def create_entity(self, *components: Any) -> int:
        entity_id = next(self.__entity_counter)
        
        self.entities[entity_id] = {}

        for component in components:
            component_ty = type(component)

            # First register this component to entity
            self.entities[entity_id][component_ty] = component

            # Then add it to the component to entity map for faster queries
            self.__add_components_to_entity_entry(component_ty, entity_id)

        return entity_id

    def remove_entity(self, entity: int):
        # We will first clear all references to our entity from component_to_entity map
        for component in self.entities[entity].keys():
            self.components_to_entity[component].remove(entity)

        # Now we can safely remove the entity
        del self.entities[entity]

    @overload
    def query_components(self, c: Type[C], c2: Type[C2], c3: Type[C3], c4: Type[C4]) -> Iterable[tuple[int, tuple[C, C2, C3, C4]]]:
        ...

    @overload
    def query_components(self, c: Type[C], c2: Type[C2], c3: Type[C3]) -> Iterable[tuple[int, tuple[C, C2, C3]]]:
        ...

    @overload
    def query_components(self, c: Type[C], c2: Type[C2]) -> Iterable[tuple[int, tuple[C, C2]]]:
        ...

    def query_components(self, *components: Type[Any]) -> Iterable[tuple[int, tuple[Any, ...]]]:
        "Query all entities with the provided set of components. For each entity found, it will return a pair of its entity ID and a tuple of its components"
        
        # First we make sure that all requested components actually exist
        if all(component in self.components_to_entity for component in components):
            
            # set.intersection takes an unlimited amount of sets as arguments, and produces "intersected" sets (i.e. whose keys appear in all given sets)
            # For example, {1, 2} and {3, 2} when intersected, produce {2}, since in both of them there's a key 2
            for entity in set.intersection(*(self.components_to_entity[component_ty] for component_ty in components)):

                # Since this is an iterator - we will yield both the entity ID and its components
                yield entity, self.get_components(entity, *components)     

    def contains_entity(self, entity: int) -> bool:
        return entity in self.entities
    
    @overload
    def get_components(self, entity: int, c: Type[C], c2: Type[C2], c3: Type[C3], c4: Type[C4]) -> tuple[C, C2, C3, C4]:
        ...

    @overload
    def get_components(self, entity: int, c: Type[C], c2: Type[C2], c3: Type[C3]) -> tuple[C, C2, C3]:
        ...

    @overload
    def get_components(self, entity: int, c: Type[C], c2: Type[C2]) -> tuple[C, C2]:
        ...
    
    def get_components(self, entity: int, *components: Type[Any]) -> tuple[Any, ...]:
        return tuple(self.entities[entity][component_ty] for component_ty in components)
    
    def get_component(self, entity: int, component_ty: Type[C]) -> C:
        return self.entities[entity][component_ty]
    
    def has_component(self, entity: int, component: Type) -> bool:
        return component in self.entities[entity]
    
    def add_components(self, entity: int, *components: Any):
        "Add an unlimited amount of components to an entity. If a component is already present - it will overwrite it with the new value"
        for component in components:
            component_ty = type(component)

            entity[component_ty] = component
            self.__add_components_to_entity_entry(component_ty, entity)

    def remove_components(self, entity: int, *components: Type[Any]):
        "Remove an unlimited amount of components from the entity based on their type"
        for component_ty in components:
            del self.entities[entity][component_ty]
            self.components_to_entity[component_ty].remove(entity)