from plugin import event

from typing import Any

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