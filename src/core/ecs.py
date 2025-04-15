from plugin import Plugin, Resources, Schedule, event, EventWriter

"A really minimal ECS module mostly inspired by [esper](https://github.com/benmoran56/esper)"

from typing import TypeVar, Type, Any, overload, Iterable, Optional
from itertools import count

MAX_COMPONENTS = 256
"This sounds like a reasonable limit to have"

# Yup, that's neccessary for adequate typing
C = TypeVar("C")
C2 = TypeVar("C2")
C3 = TypeVar("C3")
C4 = TypeVar("C4")
C5 = TypeVar("C5")

__component_bit_counter = 0b1
# This counter shifts its bit to the left for every new component
def component(cls):
    """
    A class decorator for components, which registers them by assigning a unique bit mask.
    This is required for every single component
    """
    global __component_bit_counter
    assert __component_bit_counter.bit_length() < MAX_COMPONENTS, f"Reached a component limit of {MAX_COMPONENTS}"

    # Set our class component mask to the current bit
    cls.__component_mask = __component_bit_counter

    # Shift it
    __component_bit_counter <<= 1

    return cls

def compute_signature(components: tuple[Type, ...]) -> int:
    assert all([hasattr(comp, "__component_mask") for comp in components]), "Can't use components that are registered without @component decorator"

    signature = 0
    for component in components:
        signature |= component.__component_mask
    return signature

class Archetype:
    """
    An archetype is group of entities that has the same set of components. 
    An archetype signature is a bitmask that contains a specific set of components. Thanks to python's 
    arbitrary precision integers - it's a literal gift for us that allows us to scrap set intersections
    or other slower archetype comparisons. 
    """
    def __init__(self, components: tuple[Type, ...]):
        self.signature = compute_signature(components)
        self.entities: set[int] = set()

    def contains_signature(self, component_mask: int) -> bool:
        return (self.signature & component_mask) == component_mask
    
    def get_entities(self) -> set[int]:
        return self.entities
    
    def contains_entity(self, entity: int) -> bool:
        return entity in self.entities
    
    def add_entity(self, entity: int):
        self.entities.add(entity)

    def remove_entity(self, entity: int):
        self.entities.remove(entity)

class WorldECS:
    """
    An entity container for all your ECS operations. You can learn about ECS [here](https://github.com/SanderMertens/ecs-faq?tab=readme-ov-file#what-is-ecs)
    
    This is the most primitive version of ECS, thus it doesn't even feature caching (currently). If performance becomes a bottleneck (it will pretty soon) - 
    one will be implemented here.

    Before using any of the methods - make sure to read for **undefined behaviour** parts, as there are a lot of things
    that can cause undefined behaviour when iterating entities and modifying their components.
    """
    def __init__(self, ewriter: EventWriter):
        self.ewriter = ewriter

        self.archetypes: dict[int, Archetype] = {}
        "An archetype storage, where keys are archetype bit signatures, and values are archetype objects"

        self.entities: dict[int, dict[Type[Any], Any]] = {}
        "The component storage itself. Maps entity IDs to their component dictionaries"

        self.entity_to_archetype: dict[int, Archetype] = {}
        "A map that maps an entity ID to its archetype. It makes it really convenient to remove from archetypes"

        self.dead_entities: set[int] = set()
        "Entities that are marked as removed. Dead entities aren't immediately removed for stability reasons"

        self.__entity_counter = count(start=0)

    def get_or_make_archetype(self, components: tuple[Type, ...]):
        signature = compute_signature(components)
        if signature not in self.archetypes:
            self.archetypes[signature] = Archetype(components)
        
        return self.archetypes[signature]
    
    def query_archetypes(self, signature: int) -> tuple[Archetype]:
        "Query archetypes that contain the provided signature. This method returns a tuple"
        return tuple(archetype for archetype in self.archetypes.values() if archetype.contains_signature(signature))
    
    def __assign_entity_archetype(self, entity: int):
        """
        This method will essentially register an existing entity to an archetype if it doesn't have one, or move
        to a new one instead (while removing it from the previous archetype). 

        This should always be called when an entity is created or its component set has changed.
        """
        assert entity in self.entities

        self.__discard_entity_archetype(entity, False)

        archetype = self.get_or_make_archetype(tuple(self.entities[entity].keys()))
        archetype.add_entity(entity)
        self.entity_to_archetype[entity] = archetype

    def __discard_entity_archetype(self, entity: int, clear_archetype_entry: bool = True):
        """
        If the entity ID has an archetype bound - it will remove said entity from the archetype, and optionally
        remove it from the entity_to_archetype map as well.

        The latter is neccessary for entire entity removals, but isn't that important if you're just going
        to overwrite entity's former archetype with a new one.
        """

        if entity in self.entity_to_archetype:
            self.entity_to_archetype[entity].remove_entity(entity)

            if clear_archetype_entry:
                del self.entity_to_archetype[entity]

    def create_entity(self, *components: Any) -> int:
        """
        Create an entity with the provided unlimited set of components. Make sure to not pass tuples!
        
        ## Undefined behaviour
        Don't create entities mid iteration, since there's a chance you will either miss your newly-created entities
        or iterate them in the same query.
        """

        # First we get an entity ID
        entity_id = next(self.__entity_counter)
        
        # Create a new entry in our entity dictionary with our entity components
        self.entities[entity_id] = {type(component): component for component in components}

        # Add our entity to an archetype 
        self.__assign_entity_archetype(entity_id)

        # Notify everyone
        self.ewriter.push_event(ComponentsAddedEvent(entity_id, tuple(components)))

        return entity_id

    def remove_entity(self, entity: int):
        """
        Mark an entity as removed. Note that this doesn't immediately remove the entity and you will still
        be able to access its components until the entities are actually cleared out.

        It is absolutely safe to use when iterating
        """

        self.dead_entities.add(entity)

    @overload
    def query_components(self, c: Type[C], c2: Type[C2]) -> Iterable[tuple[int, tuple[C, C2]]]:
        ...

    @overload
    def query_components(self, c: Type[C], c2: Type[C2], c3: Type[C3]) -> Iterable[tuple[int, tuple[C, C2, C3]]]:
        ...

    @overload
    def query_components(self, c: Type[C], c2: Type[C2], c3: Type[C3], c4: Type[C4]) -> Iterable[tuple[int, tuple[C, C2, C3, C4]]]:
        ...

    @overload
    def query_components(self, c: Type[C], c2: Type[C2], c3: Type[C3], c4: Type[C4], c5: Type[C5]) -> Iterable[tuple[int, tuple[C, C2, C3, C4, C5]]]:
        ...

    def query_components(self, *components: Type[Any]) -> Iterable[tuple[int, tuple[Any, ...]]]:
        """
        Query all entities with the provided set of components. 
        For each entity found, it will return a pair of its entity ID and a tuple of its components.        
        """
        
        component_signature = compute_signature(components)
        for archetype in self.query_archetypes(component_signature):
            for entity in archetype.get_entities():
                yield entity, self.get_components(entity, *components)

    def query_component(self, component_ty: Type[C]) -> Iterable[tuple[int, C]]:
        """
        Query all entities with the provided component. 
        The same as `query_components`, but for a single component.        
        """
        
        component_signature = compute_signature((component_ty, ))
        for archetype in self.query_archetypes(component_signature):
            for entity in archetype.get_entities():
                yield entity, self.get_component(entity, component_ty)

    def contains_entity(self, entity: int) -> bool:
        "Will return if the entity ID exists"
        return (entity in self.entities) and (entity not in self.dead_entities)
    

    @overload
    def get_components(self, entity: int, c: Type[C], c2: Type[C2]) -> tuple[C, C2]:
        ...

    @overload
    def get_components(self, entity: int, c: Type[C], c2: Type[C2], c3: Type[C3]) -> tuple[C, C2, C3]:
        ...

    @overload
    def get_components(self, entity: int, c: Type[C], c2: Type[C2], c3: Type[C3], c4: Type[C4]) -> tuple[C, C2, C3, C4]:
        ...

    @overload
    def get_components(self, entity: int, c: Type[C], c2: Type[C2], c3: Type[C3], c4: Type[C4], c5: Type[C5]) -> tuple[C, C2, C3, C4, C5]:
        ...
    
    def get_components(self, entity: int, *components: Type[Any]) -> tuple[Any, ...]:
        return tuple(self.entities[entity][component_ty] for component_ty in components)
    
    def get_component(self, entity: int, component_ty: Type[C]) -> C:
        return self.entities[entity][component_ty]
    
    def try_component(self, entity: int, component_ty: Type[C]) -> Optional[C]:
        "Similar to `get_component`, but returns `None` if a component isn't present"
        return self.entities[entity].get(component_ty)

    def has_component(self, entity: int, component: Type) -> bool:
        return component in self.entities[entity]
    
    def has_components(self, entity: int, *components: Type) -> bool:
        "Like `has_component`, but checks if multiple components are present at the same time"
        return all(component in self.entities[entity] for component in components)
    
    def add_components(self, entity: int, *components: Any):
        """
        Add an unlimited amount of components to an entity. 
        If a component is already present - this will panic (to avoid undefined behaviour)
        
        ## Undefined behaviour
        Adding components to entities leads to an archetype change. Entity skipping, multiple iteration of the same
        entity and much more. Only add components outside iteration
        """
        
        entity_components = self.entities[entity]

        for component in components:
            component_ty = type(component)

            assert component_ty not in entity_components, "Overwriting components produces undefined behaviour with events"
            entity_components[component_ty] = component
        
        # Since our entity has changed components - we need to move it to a different archetype
        self.__assign_entity_archetype(entity)
        
        self.ewriter.push_event(ComponentsAddedEvent(entity, tuple(self.entities[entity].values())))

    def remove_components(self, entity: int, *components: Type[Any]):
        """
        Remove an unlimited amount of components from the entity based on their type
        
        ## Undefined behaviour
        Removing entities' components leads to an archetype change. Entity skipping, multiple iteration of the same
        entity and much more. Only remove components outside iteration
        """

        # We will use this list to preserve components for our event
        removed_components = []

        for component_ty in components:
            if component_ty in self.entities[entity]:
                removed_components.append(self.entities[entity][component_ty])

                del self.entities[entity][component_ty]
            
        self.__assign_entity_archetype(entity)

        self.ewriter.push_event(ComponentsRemovedEvent(entity, tuple(removed_components)))

    def clear_dead_entities(self):
        """
        This method will get automatically at the start of every frame, but if neccessary - you can call it
        when important changes have happened to the world.

        ## Undefined behaviour
        Clearing entities mid iteration can lead to incorrect iteration of other entities (i.e. skipping other
        entities that are part of the same archetype). Only call this at the END of the iteration.
        """
        for entity in self.dead_entities:
            self.__discard_entity_archetype(entity)

            # Notify everyone
            self.ewriter.push_event(ComponentsRemovedEvent(entity, tuple(self.entities[entity].values())))

            # Now we can actually remove the entity
            del self.entities[entity]

        self.dead_entities.clear()

@event
class ComponentsAddedEvent:
    "Fired when components are added to an entity, or when a new entity is created"
    def __init__(self, entity: int, components: tuple[Any, ...]):
        self.entity = entity
        self.components = set(components)

@event
class ComponentsRemovedEvent:
    "Fired when components were removed from an entity (either through remove_components or entity removal)"
    def __init__(self, entity: int, components: tuple[Any, ...]):
        self.entity = entity
        self.components = set(components)

def clear_dead_entities(resources: Resources):
    resources[WorldECS].clear_dead_entities()
    
class ECSPlugin(Plugin):
    def build(self, app):
        app.insert_resource(WorldECS(app.get_resource(EventWriter)))
        app.add_systems(Schedule.First, clear_dead_entities)