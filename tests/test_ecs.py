from ward import test, raises
from core.ecs import WorldECS, component

from plugin import EventWriter

@component
class IsCool:
    pass

@component
class InWater:
    "Idk?"

@component
class Name:
    def __init__(self, value: str):
        self.value = value

@component
class Health:
    def __init__(self, value):
        self.value = value

@test("Test ECS entities")
def _():
    w = WorldECS(EventWriter())
    
    # Let's make sure that the entity indeed exists in our world when we create it
    entity = w.create_entity(
        Health(5), 
        Name("hello"), 
        IsCool()
    )
    assert w.contains_entity(entity)

    # Assert that the values are intact 
    assert w.get_component(entity, Name).value == "hello"
    assert w.get_component(entity, Health).value == 5
    assert w.get_component(entity, IsCool)

    # We should get exactly one result
    assert len(list(w.query_component(Health))) == 1

    # Our entity's archetype should now change
    w.remove_components(entity, Health)
    assert w.try_component(entity, Health) == None

    # Repeating the query should give us zero results
    assert len(list(w.query_component(Health))) == 0

    ## Now we'll try a different thing

    # Query for multiple components
    assert len(list(w.query_components(Name, IsCool))) == 1

    # Now, add back our Health component
    w.add_components(entity, Health(10))
    assert w.try_component(entity, Health).value == 10

    # Assert that we still get the same results, even though our archetype has changed again!
    assert len(list(w.query_components(Name, IsCool))) == 1


    ## Finally, we'll remove our entity
    w.remove_entity(entity)

    # It should not be present, if though it's only marked as dead
    assert not w.contains_entity(entity)

    w.clear_dead_entities()

    # Now it's actually removed
    assert not w.contains_entity(entity)

    # Can no longer get it
    assert len(list(w.query_components(Name, IsCool))) == 0
    assert len(list(w.query_component(Health))) == 0

def make_test_world() -> WorldECS:
    "Make a test world with 4 entities"
    w = WorldECS(EventWriter())

    ent0 = w.create_entity(Name("Entity 0"), Health(100), InWater()) 
    ent1 = w.create_entity(Name("Entity 1"), Health(50), IsCool())
    ent2 = w.create_entity(Name("Entity 2"), IsCool())
    ent3 = w.create_entity(Name("Entity 3"), Health(120), IsCool(), InWater())

    # We have created 4 different archetypes:
    # Name, Health, InWater
    # Name, Health, IsCool
    # Name, IsCool
    # Name, Health, IsCool, InWater

    return w

@test("Test ECS queries shouldn't skip entities")
def _():
    w = make_test_world()

    # Let's first query all entities by their name
    skipped_entities = [0, 1, 2, 3]
    for ent, _ in w.query_component(Name):
        skipped_entities.remove(ent)
    
    assert not skipped_entities, f"Some entities were skipped: {skipped_entities}"

@test("Test ECS we should be able to iterate all entities even if they're marked as dead during iteration")
def _():
    w = make_test_world()

    skipped_entities = [0, 1, 2, 3]
    for ent, name in w.query_component(Name):
        if w.contains_entity(1):
            w.remove_entity(1)
        skipped_entities.remove(ent)
    
    assert not skipped_entities, f"Some entities were skipped: {skipped_entities}"


# These tests purely exist so that the problem of undefined behaviour can be tackled later
# I don't want them to be red, so let's just say "it's expected behaviour"

@test("Test ECS queries will skip entities when changing their archetypes mid iteration")
def _():
    w = make_test_world()

    # Here we're going to skip entity 3, even though it certainly does exist
    skipped_entities = [0, 1, 2, 3]

    # So, our entity 3 has a unique archetype (Name, Health, IsCool, InWater)
    # Archetype 2 is basically the same, but without the InWater component.
    # If we're going to remove InWater component AFTER iterating entity 1, we're going to skip entity 3

    for ent, name in w.query_component(Name):
        if ent == 2:
            w.remove_components(3, InWater)

        skipped_entities.remove(ent)
    
    assert skipped_entities == [3]

@test("Test ECS queries will iterate multiple times entities when changing their archetypes mid iteration")
def _():
    w = make_test_world()

    # Here, entity 1 will be iterated 2 times
    skipped_entities = [0, 1, 2, 3, 1]

    # When we iterate over 1, we'll give it InWater component, which will move it to an archetype of entity
    # 3. Thus, it wil lead to a dublicate iteration

    for ent, name in w.query_component(Name):
        if ent == 2:
            w.add_components(1, InWater())

        skipped_entities.remove(ent)
    
    assert not skipped_entities
