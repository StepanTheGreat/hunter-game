from plugin import Plugin, Resources, Schedule, EventWriter

from core.ecs import WorldECS

from plugins.server.events import ClientConnectedEvent, ClientDisconnectedEvent, AddedClientEvent, RemovedClientEvent

from plugins.server.components import Client

class ClientList:
    "A server-side list of all client addresses that are connected to the server"

    def __init__(self):
        self.addr_to_ent: dict[tuple[str, int]: int] = {}
        self.ent_to_addr: dict[int: tuple[str, int]] = {}

    def _add_client(self, addr: tuple[str, int], ent: int):
        self.addr_to_ent[addr] = ent 
        self.ent_to_addr[ent] = addr

    def _remove_client(self, addr: tuple[str, int]):
        ent = self.addr_to_ent.pop(addr)
        self.ent_to_addr.pop(ent)

    def contains_client_ent(self, ent: int) -> bool:
        return ent in self.ent_to_addr

    def contains_client_addr(self, addr: tuple[str, int]) -> bool:
        return addr in self.addr_to_ent

    def get_client_ent(self, addr: tuple[str, int]) -> int:
        "Get the client's entity from this address. This can raise an exception if the client isn't present"

        return self.addr_to_ent[addr]
    
    def get_client_addr(self, ent: int) -> tuple[str, int]:
        "Get the client's address from this entity. This can raise an exception if the client isn't present"

        return self.ent_to_addr[ent]

def on_client_connected(resources: Resources, event: ClientConnectedEvent):
    """
    When a client connects - we would like to create an entity and add it to the client list
    """

    world = resources[WorldECS]
    ewriter = resources[EventWriter]
    clientlist = resources[ClientList]

    client_addr = event.addr
    assert not clientlist.contains_client_addr(client_addr)

    # Create our entity
    client_ent = world.create_entity(Client(client_addr))

    # Bind it to our address
    clientlist._add_client(client_addr, client_ent)

    ewriter.push_event(AddedClientEvent(client_addr, client_ent))

def on_client_disconnected(resources: Resources, event: ClientDisconnectedEvent):
    """
    When the client disconnects, we would like to remove it from the client list, and also
    remove its client entity as well
    """

    world = resources[WorldECS]
    ewriter = resources[EventWriter]
    clientlist = resources[ClientList]

    client_addr = event.addr
    assert clientlist.contains_client_addr(client_addr)

    # Get its client entity
    client_ent = clientlist.get_client_ent(client_addr)

    # Remove it immediately from the world
    with world.command_buffer() as cmd:
        cmd.remove_entity(client_ent)

    # Remove it from the client list
    clientlist._remove_client(client_addr)

    ewriter.push_event(RemovedClientEvent(client_addr, client_ent))

class ClientListPlugin(Plugin):
    def build(self, app):
        app.insert_resource(ClientList())

        app.add_event_listener(ClientConnectedEvent, on_client_connected)
        app.add_event_listener(ClientDisconnectedEvent, on_client_disconnected)

