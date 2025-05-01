"Common components across both sessions"

from core.ecs import WorldECS, component, ComponentsRemovedEvent, ComponentsAddedEvent

from plugin import Plugin, Resources, EventWriter, event, run_if, resource_exists
from typing import Optional

@component
class NetEntity:
    """
    A shared entity across the network. This entity has a unique identifier, which makes it possible
    from the server to communicate commands and its precise targets
    """
    def __init__(self, uid: int):
        assert 0 <= uid < 2**16, "Net UID is only valid in ranges between 0 and 2**16"
        self.uid = uid

    def get_uid(self) -> int:
        return self.uid
    
@component
class NetSyncronized:
    """
    This component tells the server that the entity with this component should get syncronized
    across network every fixed frame
    """

class NetworkEntityMap:
    """
    A network map that maps all network entities to ECS entity IDS and in reverse. 

    It is important to clear this map every time a new session is created, as it can cause
    instability if the map is reused without cleanup in multiple sessions
    """
    def __init__(self):
        self.uid_to_ent: dict[int, int] = {}
        self.ent_to_uid: dict[int, int] = {}

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
        """
        Reset the map. This should be called every time the host is created/closed. 
        """
        self.ent_to_uid.clear()
        self.uid_to_ent.clear()

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

@run_if(resource_exists, NetworkEntityMap)
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

@run_if(resource_exists, NetworkEntityMap)
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

class SessionComponentPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(ComponentsAddedEvent, on_network_entity_added)
        app.add_event_listener(ComponentsRemovedEvent, on_network_entity_removed)