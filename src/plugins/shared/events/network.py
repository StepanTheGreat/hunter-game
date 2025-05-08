from plugin import event

@event
class ClientConnectedEvent:
    "A client has connected to the server. It's fired on the host (i.e. when you're the server)"
    def __init__(self, addr: tuple[str, int]):
        self.addr = addr

@event
class ClientDisconnectedEvent:
    "A client has disconnected from the server. It's fired on the host (i.e. when you're the server)"
    def __init__(self, addr: tuple[str, int]):
        self.addr = addr

@event
class ServerConnectedEvent:
    "A connection to the server was succesfully established (i.e. when you're the client)"

@event
class ServerDisonnectedEvent:
    "Connection was lost with the server (or forcefully disconnected) (i.e. when you're the client)"

@event
class ServerConnectionFailEvent:
    "A connection to the server was unsuccesful (i.e. when you're the client)"

@event
class AddedNetworkEntityEvent:
    "Fired when a network entity has been created"
    def __init__(self, ent: int, uid: int, comps: set):
        self.ent = ent
        self.uid = uid
        self.comps: set = comps

@event
class RemovedNetworkEntityEvent:
    "Fired when a network entity got deleted from the ECS world"
    def __init__(self, ent: int, uid: int, comps: set):
        self.ent = ent
        self.uid = uid
        self.comps: set = comps