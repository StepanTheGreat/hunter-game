from plugins.shared.components import *

from core.ecs import component

@component
class Client:
    """
    A component representing a network client. A server client can be simply modelled as an entity:
    they can have components like `dead`, it's extremely easy to fetch clients based on their roles
    using components, and it's also extremely easy to bind to them physical entities.
    """
    def __init__(self, addr: tuple[str, int]):
        self.addr = addr

    def get_addr(self) -> tuple[str, int]:
        return self.addr

@component
class OwnsEntity:
    """
    A component attached to clients that essentially points to a physical player entity.
    An absence on this component for example, signals that the client is dead or just joined
    (so they're going to get their first entity)
    """
    def __init__(self, ent: int):
        self.ent: int = ent

    def get_ent(self) -> int:
        return self.ent
    
@component
class OwnedByClient:
    "A component attached to physical entities that points to a client entity"
    def __init__(self, client_ent: int):
        self.client_ent: int = client_ent

    def get_client_ent(self) -> int:
        return self.client_ent

@component
class RobberClient:
    "The client that was chosen to be the robber"