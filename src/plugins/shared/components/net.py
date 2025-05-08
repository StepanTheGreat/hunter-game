"Network components"

from core.ecs import WorldECS, component, ComponentsRemovedEvent, ComponentsAddedEvent

from plugin import Plugin, Resources, EventWriter

from plugins.shared.events import AddedNetworkEntity, RemovedNetworkEntity

from itertools import count

from typing import Optional

UID_LIMIT = 2**16
"The UID limit for an entity"

@component
class NetEntity:
    """
    A shared entity across the network. This entity has a unique identifier, which makes it possible
    from the server to communicate commands and its precise targets
    """
    def __init__(self, uid: int):
        assert 0 <= uid < UID_LIMIT, f"Net UID is only valid in ranges between 0 and {UID_LIMIT}"

        self.uid = uid

    def get_uid(self) -> int:
        return self.uid
    
@component
class NetSyncronized:
    """
    This component tells the server that the entity with this component should get syncronized
    across network every fixed frame
    """

class EntityUIDManager:
    """
    The UID manager manages all entity UID operations. Generating new UIDs, mapping ECS entities
    to virtual UIDs or the other way around.

    This allows for highly event-driven approach, by tracking network to UID relationships directly.
    An entity with an UID component dead would mean we can get a direct event, to which the server
    for example can listen and do some actions (telling the clients to kill a specific entity).

    The most important note is that this manager should be reset ON EVERY SESSION, so it's important
    to not forget to clean it up (especially on the client).
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

    def reset(self):
        "Reset this UID manager. Should be called every time there's a new network session"

        self.ent_to_uid.clear()
        self.uid_to_ent.clear()
        self._uid_counter = count(0)

    def consume_entity_uid(self) -> int:
        next_uid = next(self._uid_counter)

        assert next_uid < EntityUIDManager.ENTITY_UID_LIMIT, f"Reached the UID limit of {EntityUIDManager.ENTITY_UID_LIMIT}"

        return next_uid

def reset_entity_uid_manager(resources: Resources):
    "Reset the entity UID manager if there's a new session"

    resources[EntityUIDManager].reset()

def on_network_entity_removed(resources: Resources, event: ComponentsRemovedEvent):
    # If an entity with a NetEntity component gets removed - we would like to push an event
    # with its UID

    netman = resources[EntityUIDManager]
    ewriter = resources[EventWriter]
    
    if NetEntity in event.components:
        ent = event.entity
        uid = netman.get_uid(ent)

        netman._remove_entry_by_ent(ent)
        ewriter.push_event(RemovedNetworkEntity(ent, uid))

def on_network_entity_added(resources: Resources, event: ComponentsAddedEvent):
    netman = resources[EntityUIDManager]
    ewriter = resources[EventWriter]
    world = resources[WorldECS]
    
    if NetEntity in event.components:
        ent = event.entity

        uid_comp = world.get_component(ent, NetEntity)
        uid = uid_comp.get_uid()

        netman._push_pair(ent, uid)
        ewriter.push_event(AddedNetworkEntity(ent, uid))

class NetworkComponentsPlugin(Plugin):
    def build(self, app):
        app.insert_resource(EntityUIDManager())
        app.add_event_listener(ComponentsAddedEvent, on_network_entity_added)
        app.add_event_listener(ComponentsRemovedEvent, on_network_entity_removed)