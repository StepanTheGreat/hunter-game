"Network components"

from core.ecs import component
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