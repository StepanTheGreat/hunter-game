from plugin import Plugin, Resources, Schedule, event, EventWriter

"A really minimal ECS module mostly inspired by [esper](https://github.com/benmoran56/esper)"

from typing import TypeVar, Type, Any, overload, Iterable, Optional, Union
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

__signature_cache = {}

def compute_signature(components: Union[tuple[Type, ...], Type]) -> int:
    "Compute a bitmask signature for the provided tuple of components. This internally uses caching for all results"

    signature = __signature_cache.get(components)
    if signature is None:

        if type(components) is tuple:
            assert all([hasattr(comp, "__component_mask") for comp in components]), "Can't use components that are registered without @component decorator"

            signature = 0 # It's zero, since passing an empty tuple should be valid
            for component in components:
                signature |= component.__component_mask
        else:
            assert hasattr(components, "__component_mask"), "Can't use a component that is not registered with @component decorator"
            signature = components.__component_mask

        __signature_cache[components] = signature    
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

    def matches_signatures(self, components_sig: int, without_sig: int) -> bool:
        """
        Check whether this archetype matches the 2 provided signatures. To clear out any confusion - there are
        actually 3 masks, but we're using 2, since a `requested_components` and `with_components` mask can 
        essentially get combined using a bit OR operation into one, reducing the numbers of comparisons neccessary.
        This isn't the case however for `without_components` mask, as it needs to be treated separately.
        """
        return (
            ((self.signature & components_sig) == components_sig) and
            ((self.signature & without_sig) == 0)
        )
    
    def get_entities(self) -> set[int]:
        return self.entities
    
    def contains_entity(self, entity: int) -> bool:
        return entity in self.entities
    
    def add_entity(self, entity: int):
        self.entities.add(entity)

    def remove_entity(self, entity: int):
        self.entities.remove(entity)

class CommandBuffer:
    """
    The purpose of a command buffer is to simplify entity command dispatching in iterated queries.

    Operations like entity removal, component addition/removal are inherently unstable, as queries aren't
    evaluated immediately, thus it can directly cause instability. Entities can get iterated multiple times
    or not get iterated at all.

    For this sole reason, a command buffer exists to simply queue all commands using Python's nice
    context manager syntax. This way, you don't need to manage your own lists and state, to simply add/remove
    a component from an entity.
    """
    def __init__(self, world: "WorldECS"):
        self.world = world
        self.created_entities: list[tuple[int, tuple[Any, ...]]] = []
        self.added_components: list[tuple[int, tuple[Any, ...]]] = []
        self.removed_components: list[tuple[int, tuple[Any, ...]]] = []

    def create_entity(self, *components: Any) -> int:
        """
        Create a new entity with the provided components and return its ID. 
        
        While the ID is returned immediately - it doesn't mean the entity is already in the world.
        It will be added at the end of the `with` scope only.
        """

        entity_id = self.world.consume_new_entity_id()
        self.created_entities.append((entity_id, components))
        return entity_id

    def add_components(self, ent: int, *components: Any):
        "Add an undefined amount of components to an entity. This command will be dispatched AT THE END of the `with` scope"
        self.added_components.append((ent, components))

    def remove_components(self, ent: int, *components: Any):
        "Remove an undefined amount of components from an entity. This command will be dispatched AT THE END of the `with` scope"
        self.removed_components.append((ent, components))

    def remove_entity(self, ent: int):
        """
        Remove the specified entity from the world. 
        
        While entities are still internally marked dead by the world - you might still find 
        this method and the command buffer overall useful for immediate dead entity cleanup, 
        since you don't need to explicitly call the `clear_dead_entities` method on the world each time. 
        """

        # Since the world already has an internal marker over dead entities - there's no reason for us to
        # queue it separately. This method exists purely to unify API
        self.world.remove_entity(ent)

    def flush(self):
        "Flush all the commands to the world."

        # First create all entities
        for entity_id, components in self.created_entities:
            self.world.create_entity(*components, entity_id=entity_id)

        # Add components to entities
        for ent, components in self.added_components:
            self.world.add_components(ent, *components)

        # Remove commponents from entities
        for ent, components in self.removed_components:
            self.world.remove_components(ent, *components)

        # Delete requested entities from the world
        self.world.clear_dead_entities()

    def __exit__(self, exception_ty: type, exception_val: Any, traceback):
        self.flush()

        # If there are any errors - they should be propagated
        return False

    def __enter__(self):
        return self

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

        self.__query_cache = {}
        """
        We will store here components as keys, and lists of query results as values. If nothing changes - there's
        no reason for us to re-query entities. This is especially important for rendering logic, as it doesn't
        modify entities much, but still queries them more often than the game's logic itself.
        """

        self.__entity_counter = count(start=0)

    def __get_or_make_archetype(self, components: tuple[Type, ...]):
        signature = compute_signature(components)
        if signature not in self.archetypes:
            self.archetypes[signature] = Archetype(components)
        
        return self.archetypes[signature]
    
    def __query_archetypes(self, components_sig: int, with_sig: int, without_sig: int) -> tuple[Archetype]:
        "Query archetypes that contain the provided signature. This method returns a tuple"

        components_sig = components_sig | with_sig
        # The reason we're combining these 2 masks into one is that they essentially work the same way.
        # The `without` filter however, needs to be treated separately

        return tuple(archetype for archetype in self.archetypes.values() if archetype.matches_signatures(components_sig, without_sig))
    
    def __assign_entity_archetype(self, entity: int):
        """
        This method will essentially register an existing entity to an archetype if it doesn't have one, or move
        to a new one instead (while removing it from the previous archetype). 

        This should always be called when an entity is created or its component set has changed.
        """
        assert entity in self.entities

        self.__discard_entity_archetype(entity, False)

        archetype = self.__get_or_make_archetype(tuple(self.entities[entity].keys()))
        archetype.add_entity(entity)
        self.entity_to_archetype[entity] = archetype

        self.__clear_cache()

    def __discard_entity_archetype(self, entity: int, clear_archetype_entry: bool = True):
        """
        If the entity ID has an archetype bound - it will remove said entity from the archetype, and optionally
        remove it from the entity_to_archetype map as well.

        The latter is neccessary for entire entity removals, but isn't that important if you're just going
        to overwrite entity's former archetype with a new one.
        """

        if entity in self.entity_to_archetype:
            self.entity_to_archetype[entity].remove_entity(entity)
            self.__clear_cache()

            if clear_archetype_entry:
                del self.entity_to_archetype[entity]

    def __clear_cache(self):
        "Should be called every time a change to either an archetype or an entity is done"
        self.__query_cache.clear()

    def consume_new_entity_id(self) -> int:
        "An internal method for generating a new unique entity ID. Don't call this unless you know what you're doing."
        return next(self.__entity_counter)
    
    def command_buffer(self) -> CommandBuffer:
        """
        Create a command buffer for queing entity commands like remove/create/add components/remove components.

        Because applying said commands while iterating a query can pose undefined behaviour - it's recommended
        to use a command buffer with the python's `with` syntax to avoid most of the troubles.

        If you're not modifying/creating/deleting entities in queries - there's no reason for you to buffer
        your commands.
        """
        return CommandBuffer(self)

    def create_entity(self, *components: Any, entity_id: int = None) -> int:
        """
        Create an entity with the provided unlimited set of components. Make sure to not pass tuples!

        This method takes a named parameter `entity_id`, which you absolutely shouldn't touch as it will
        directly overwrite an existing entity if misused! (This is used internally in combination with `CommandBuffer`) 
        
        ## Undefined behaviour
        Don't create entities mid iteration, since there's a chance you will either miss your newly-created entities
        or iterate them in the same query.
        """

        # First we get an entity ID (either provided or automatic)
        if entity_id is not None:
            assert type(entity_id) is int
        else:
            entity_id = self.consume_new_entity_id()
        
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
    def query_components(
        self, 
        c: Type[C], c2: Type[C2],
        including: tuple[Type, ...] = (), 
        excluding: tuple[Type, ...] = ()
    ) -> Iterable[tuple[int, tuple[C, C2]]]:
        ...

    @overload
    def query_components(
        self, 
        c: Type[C], c2: Type[C2], c3: Type[C3],
        including: tuple[Type, ...] = (), 
        excluding: tuple[Type, ...] = ()
    ) -> Iterable[tuple[int, tuple[C, C2, C3]]]:
        ...

    @overload
    def query_components(
        self, 
        c: Type[C], c2: Type[C2], c3: Type[C3], c4: Type[C4], 
        including: tuple[Type, ...] = (), 
        excluding: tuple[Type, ...] = ()
    ) -> Iterable[tuple[int, tuple[C, C2, C3, C4]]]:
        ...

    @overload
    def query_components(
        self, 
        c: Type[C], c2: Type[C2], c3: Type[C3], c4: Type[C4], c5: Type[C5], 
        including: tuple[Type, ...] = (), 
        excluding: tuple[Type, ...] = ()
    ) -> Iterable[tuple[int, tuple[C, C2, C3, C4, C5]]]:
        ...

    def query_components(
        self, 
        *components: Type[Any], 
        including: tuple[Type, ...] = (), 
        excluding: tuple[Type, ...] = ()
    ) -> Iterable[tuple[int, tuple[Any, ...]]]:
        """
        Query all entities with the provided set of components. 
        For each entity found, it will return a pair of its entity ID and a tuple of its components.

        This method also includes 2 filters: `including` and `excluding`. Both of these take tuples of types
        or types directly allowing you to filter your query. 
        The query will ignore entities with components that are in the `excluding` filter, or entities
        that don't have components specified in the `including` filter.        
        """
        
        result = self.__query_cache.get((components, including, excluding))
        if result is None:
            result = self.__query_cache.setdefault(
                (components, including, excluding), 
                list(self.__query_components(components, including, excluding))
            )
        return result

    def __query_components(self, components: tuple[Type[Any]], including: tuple[Type, ...], excluding: tuple[Type, ...]):
        component_sig = compute_signature(components)
        with_sig = compute_signature(including)
        without_sig = compute_signature(excluding)

        for archetype in self.__query_archetypes(component_sig, with_sig, without_sig):
            for entity in archetype.get_entities():
                yield entity, self.get_components(entity, *components)

    def query_component(
        self, 
        component_ty: Type[C], 
        including: Union[Type, tuple[Type, ...]] = (), 
        excluding: Union[Type, tuple[Type, ...]] = ()
    ) -> Iterable[tuple[int, C]]:
        """
        Query all entities with the provided component. 
        The same as `query_components`, but for a single component.        
        """
        result = self.__query_cache.get((component_ty, including, excluding))
        if result is None:
            result = self.__query_cache.setdefault(
                (component_ty, including, excluding), 
                list(self.__query_component(component_ty, including, excluding))
            )
        return result

    def __query_component(self, component_ty: Type[C], including: tuple[Type, ...], excluding: tuple[Type, ...]):
        component_sig = compute_signature((component_ty, ))
        with_sig = compute_signature(including)
        without_sig = compute_signature(excluding)

        for archetype in self.__query_archetypes(component_sig, with_sig, without_sig):
            for entity in archetype.get_entities():
                yield entity, self.get_component(entity, component_ty)

    def contains_entity(self, entity: int) -> bool:
        "Check if the entity ID is present or alive"
        return (entity in self.entities) and (entity not in self.dead_entities)
    
    def contains_entities(self, *entities: int) -> bool:
        "Check if multiple entity IDs is present or alive"
        return all((entity in self.entities) and (entity not in self.dead_entities) for entity in entities)

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
        app.add_systems(Schedule.FixedUpdate, clear_dead_entities, priority=-10)