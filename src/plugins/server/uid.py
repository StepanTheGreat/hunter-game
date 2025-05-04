from core.ecs import WorldECS, component, ComponentsRemovedEvent, ComponentsAddedEvent

from plugin import Plugin, Resources, EventWriter, event
from typing import Optional

from plugins.shared.components import UID_LIMIT

from itertools import count

class EntityUIDManager:
    """
    The UID manager manages all entity UID operations. Generating new UIDs, mapping ECS entities
    to virtual UIDs or the other way around.

    This allows for highly event-driven approach, by tracking network to UID relationships directly.
    An entity with an UID component dead would mean we can get a direct event, to which the server
    for example can listen and do some actions (telling the clients to kill a specific entity).

    The most important note is that this manager should be reset ON EVERY SESSION, so using it on a server
    app that gets reset every single time isn't an issue.
    """
    ENTITY_UID_LIMIT = UID_LIMIT

    def __init__(self):
        self.uid_to_ent: dict[int, int] = {}
        self.ent_to_uid: dict[int, int] = {}
        
        self._uid_counter = count(0)

    def _push_pair(self, ent: int, uid: int):
        self.uid_to_ent[uid] = ent
        self.ent_to_uid[ent] = uid

    def get_uid(self, ent: int) -> Optional[int]:
        return self.ent_to_uid.get(ent)
    
    def get_ent(self, uid: int) -> Optional[int]:
        return self.uid_to_ent.get(uid)

    def _remove_entry_by_ent(self, ent: int):
        "Delete entity pair from the registry by its Entity ID"

        uid = self.get_uid(ent)

        del self.ent_to_uid[ent]
        del self.uid_to_ent[uid]

    def consume_entity_uid(self) -> int:
        next_uid = next(self._uid_counter)

        assert next_uid < NetworkEntityMap.ENTITY_UID_LIMIT, f"Reached the UID limit of {NetworkEntityMap.ENTITY_UID_LIMIT}"

        return next_uid

@event
class AddedNetworkEntity:
    "Fired when a network entity has been created"
    def __init__(self, ent: int, uid: int):
        self.ent = ent
        self.uid = uid

@event
class RemovedNetworkEntity:
    "Fired when a network entity got deleted from the ECS world"
    def __init__(self, ent: int, uid: int):
        self.ent = ent
        self.uid = uid

def on_network_entity_removed(resources: Resources, event: ComponentsRemovedEvent):
    # If an entity with a NetEntity component gets removed - we would like to push an event
    # with its UID

    netmap = resources[NetworkEntityMap]
    ewriter = resources[EventWriter]
    
    if NetEntity in event.components:
        ent = event.entity
        uid = netmap.get_uid(ent)

        netmap._remove_entry_by_ent(ent)
        ewriter.push_event(RemovedNetworkEntity(ent, uid))

def on_network_entity_added(resources: Resources, event: ComponentsAddedEvent):
    netmap = resources[NetworkEntityMap]
    ewriter = resources[EventWriter]
    world = resources[WorldECS]
    
    if NetEntity in event.components:
        ent = event.entity

        uid_comp = world.get_component(ent, NetEntity)
        uid = uid_comp.get_uid()

        netmap._push_pair(ent, uid)
        ewriter.push_event(AddedNetworkEntity(ent, uid))

class UIDManagerPlugin(Plugin):
    def build(self, app):
        app.insert_resource(EntityUIDManager())
        app.add_event_listener(ComponentsAddedEvent, on_network_entity_added)
        app.add_event_listener(ComponentsRemovedEvent, on_network_entity_removed)