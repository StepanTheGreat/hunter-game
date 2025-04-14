from ward import test, raises
from core.ecs import WorldECS

from plugin import EventWriter

class CustomComponent:
    def __init__(self, value):
        self.value = value

@test("Test basic ECS")
def _():
    w = WorldECS(EventWriter())

    # Let's say we have components Name and Value
    Name, Value = str, int

    
    # Let's make sure that the entity indeed exists in our world when we create it
    entity = w.create_entity(5, "hello", CustomComponent([1, 2]))
    assert w.contains_entity(entity)
    
    # If we're going to query it's components - we must currently get only ONE result, with exact values

    query = list(w.query_components(Name, Value))
    assert len(query) == 1
    query = query[0]

    assert query[0] == entity
    assert query[1][0] == "hello"
    assert query[1][1] == 5

    # Get components should work as well
    assert w.get_components(entity, Name, Value) == ("hello", 5)

    # Now, our query should fail (not literally), since we removed the Name component!
    w.remove_components(entity, Name)
    for ent, (name, value) in w.query_components(Name, Value):
        assert False, "Shouldn't be able to query, since our entity doesn't have the components"

    # This should now crash
    with raises(KeyError):
        w.get_component(entity, Name)

    # Of course, it should not exist if we remove it from our arrays
    w.remove_entity(entity)
    assert not w.contains_entity(entity)

    w.create_entity(1, "hi", CustomComponent([0]))
    w.create_entity(2, "hi2", CustomComponent([0]))
    w.create_entity(3, "hi3", CustomComponent([0]))

    assert len(list(w.query_components(Value, Name))) == 3