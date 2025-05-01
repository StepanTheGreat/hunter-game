"Common components across both sessions"

from core.ecs import component

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