"""
## Networking

I have little networking experience, so it's my first time building a full on UDP client-server framework.

The code here will only target 2 reliability types: Reliable (unordered) and Unreliable. Which allows the user to
either send reliable packets (like actions), or unreliable actions (like movement packets) quickly enough.
Here Im going to document a few aspects of my implementation of this framework.

## Packet
A packet is just data that we send over the network. It however, contains a bit more information due to our
framework's requirements. 
Let's cover most important aspects of our reliable frameworks first:

### Data corruption
The solution we use here is extremely simple: before constructing a packet, we generate a hash of that packet, and
insert it at the start: `[hash][data]`. The idea is, that a corrupted packet has almost non-existent chance of getting 
through and still passing the checksum check if it was corrupted, which is ideal for us.

### Reliability
The basic idea behind reliability is that we bind a unique sequence ID to every single packet we send.
Then, we wait from the end-receiver for the acknowledgement packet. Acknowledgement packets are unreliable on their
own, so they can as well fail to get delievered. So, the basic approach is to simply resend this acknowledgement
again back.

When, we have received our acknowledgement - we will register that seq ID as received. Because we maintain a large
queue - we will not be able to remove it immediately. BUT, when we DO encounter the packet that was acknowledged - 
we will just ignore it, and send any other packet

### Dublicates
It's not common to receive dublicate packets, especially when solving the reliability problem, as it requires
one to resend the same packet multiple times. For this exact purpose we have a separate rotating set, but now
for received packets by us.
When we encounter a new packet - we register it in this rotating set and send an acknowledgement. 
If we encounter the same packet again - we acknowledge it again, but don't return its data to the end-user
using this framework (because they don't need dublicates).

### Rotating sets
In this networking scheme we're using "rotating sets". These are sets that simply get rotated. The essential problem
they solve is as follows: imagine a long connection with over thousands of packets sent and recived. The sequence
ID is not infinite, and thus will need to wrap around one day. BUT, how? If all our acknowledged packets are still
bound to it? Well, that's the point of the rotating set - it only keeps the most relevant items in it. Internally
it achieves it with a large queue of N items. Every insertion will shift this queue to the left, adding the most
relevant item to the right. Upon filling up the N available space - it's going to remove from its set all the items
on the left side of the queue (with every insertion). This way, we only keep the entry that we need.

A rotating set of thousands item is already enough for most cases, as it's not heavy on memory, while also keeps
only the most relevant around.

### Connection
Since UDP doesn't understand the concept of a "connection" (it only throws messages in people's faces), we need
to introduce it to one. Before we can even communicate - we need to establish a connection. This is essentially an
unreliable empty packet of type `Connection`, that's going to be sent all over again, until we either reach a limit
or actually agree on a connection.

So, what do we do with this connection?
Well, it allows us to know our active receivers and maintain separate states for each and every one of them.
For example, acknowledge databases are local PER every connection.
Another perk is that we can understand when a connection is lost - using a concept known as heartbeat! A heartbeat
is essentially a special type of packet that is sent in specific intervals (like once every second). The idea 
behind it is that if we don't receive a heartbeat for a long duration of time - the user might be disconnected,
and thus we can end our communication.

For a disconnection, we can either send a `Disconnection` message to end our communications immediately, or... we can
just quit until the hearbeat thing fires... yes, that should do the trick

### Congestion control
For congestion control we set up an initial amount of bytes we can send per tick. This means that per fixed tick,
we absolutely can send multiple packets at the same time if we have them. This is a really simple congestion control
however

## Special sequence IDs
Due to my laziness, I decided to maintain both packet types in the same message queue. This essentially means that
all packets are treated equally, though at expense of 1 additional byte on transfer.
For this reason, absolutely every single packet has a sequence ID, even those that are supposed to be unreliable.
Solution? We assign a special ID to unreliable packets - zero. That means that our sequence counting starts from 1,
and wraps around back to 1. This does mean that we're sending more data (by 1 byte), but if it's going to bite me - 
I'm going to come up with a separate structure for both.
"""

from typing import Optional, Callable, Iterable, Union

from .circleset import CircleSet
from collections import deque

from enum import Enum, auto

import socket
import random as rnd

WRAP_IDS = 2**16

BASE_UDP_HEADER_SIZE = 32
"""
I got this approximate number from [this](https://stackoverflow.com/questions/4218553/what-is-the-size-of-udp-packets-if-i-send-0-payload-data-in-c) 
answer. Because we're doing a bit of congestion control - it's important to approximate the possible amount of
bytes that we can safely transfer in a single tick.
"""

BYTE_ORDER = "little"

BYTES_PER_MESSAGE = 1024
"""
Because fragmentation can occur on large amounts of data - we're limiting here the amount of bytes we can send to this number.
(Also I don't want to work on fragmentation anyway)
"""

RECV_BYTES = BYTES_PER_MESSAGE+64 
# Sorry for the magic number, we're just compensating for headers and other possible garbage

_global_loss_rate = 0
_global_dublicates_rate = 0
_global_corruption_rate = 0

def should_corrupt() -> bool:
    return rnd.random() < _global_loss_rate

def should_dublicate() -> bool:
    return rnd.random() < _global_dublicates_rate

def should_lose_packet() -> bool:
    return  rnd.random() < _global_loss_rate

def set_loss_rate(to: float):
    assert 0 <= to <= 1
    global _global_loss_rate
    _global_loss_rate = to

def set_corruption_rate(to: int):
    assert 0 <= to <= 1
    global _global_corruption_rate
    _global_corruption_rate = to

def set_dublicates_rate(to: int):
    assert 0 <= to <= 1
    global _global_dublicates_rate
    _global_dublicates_rate = to

def reset_unreliability():
    global _global_corruption_rate, _global_dublicates_rate, _global_loss_rate
    _global_corruption_rate = 0
    _global_dublicates_rate = 0
    _global_loss_rate = 0

def fnv1_hash(data: bytes) -> int: 
    "This is a Fowler-Noll-Vo hash function. For curious: python's `hash` uses a different salt every session, so it's unstable"
    FNV_PRIME = 0x100000001B3
    FNV_OFFSET =  0xCBF29CE484222325

    ret_hash = FNV_OFFSET
    for byte in data:
        ret_hash = ((ret_hash * FNV_PRIME) ^ byte) & 0xFFFFFFFF

    return ret_hash 

def get_current_addr() -> str:
    "Get the current IP address of this device"
    return socket.gethostbyname(socket.gethostname())

def make_async_socket(
    addr: tuple[str, int], 
    broadcaster: bool = False,
    shared: bool = False
) -> socket.socket:
    """
    This function simply creates a new non-blocking UDP socket:
    - `addr`: the address on which create and bind this socket
    - `broadcaster`: can this socket send broadcasts? `True` if yes
    - `shared`: can this socket's address be reused? `True` if yes
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, shared)

    sock.bind(addr)
    sock.setblocking(False)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, broadcaster)

    return sock

class PacketType(Enum):
    Broadcast = auto()
    "This variant only exists to make it possible to use the same packet format for broadcasters as well"

    Acknowledgment = auto()
    "A packet has been acknowledged"
    
    Message = auto()
    "This is simply a data packet"

    Heartbeat = auto()
    "A special type of message that is sent regularly to tell that the connection still persists"

    ConnectionRequest = auto()
    "A client request to establish a connection"
    
    ConnectionResponse = auto()
    "The server has agreed/disagreed on a connection"

    Disconnection = auto()
    """
    A message that's sent to notify the receiving side of closing the connection.
    This allows the closing side to disconnect way faster in most cases (if the packet loss is small).
    It's still sent once via unreliable channel, so it's more of a higher chance.
    """

def open_packet(b: bytes) -> Optional[tuple[int, PacketType, bytes]]:
    "Tries opening a packet, and if succesful - returns its sequence ID, type and data"

    assert len(b) >= 4+2+1, "[hash][hash][hash][hash][seq][seq][ty]...[data], not enough bytes!"

    data = b[4:]
    message_hash = int.from_bytes(b[:4], BYTE_ORDER)
    message_id = int.from_bytes(data[:2], BYTE_ORDER)

    try:
        # If not a proper packet type - drop it
        message_ty = PacketType(data[2])
    except ValueError:
        return

    if message_hash != fnv1_hash(data):
        # The signatures should pass
        return

    return message_id, message_ty, data[3:]
        
def make_reliable_packet(id: int, ty: PacketType, data: bytes) -> bytes:
    packet_id = id.to_bytes(2, BYTE_ORDER)
    packet_ty = ty.value.to_bytes(1, BYTE_ORDER)

    packet = packet_id + packet_ty + data
    packet_hash = fnv1_hash(packet)
    packet_hash = packet_hash.to_bytes(4, BYTE_ORDER)

    return packet_hash + packet

def make_unreliable_packet(ty: PacketType, data: bytes) -> bytes:
    "The same as `make_reliable_packet`, but it simply sets its sequence ID as a zero"
    return make_reliable_packet(0, ty, data)

def make_acknowledgement_packet(seq_id: int) -> bytes:
    "Construct an acknowledgement packet"
    return make_unreliable_packet(PacketType.Acknowledgment, seq_id.to_bytes(2, BYTE_ORDER))

def make_heartbeat_packet() -> bytes:
    return make_unreliable_packet(PacketType.Heartbeat, bytes())

def make_connection_request_packet() -> bytes:
    return make_unreliable_packet(PacketType.ConnectionRequest, bytes())

def make_connection_response_packet(accept: bool) -> bytes:
    return make_unreliable_packet(PacketType.ConnectionResponse, bytes([accept]))

def make_broadcast_packet(data: bytes) -> bytes:
    return make_unreliable_packet(PacketType.Broadcast, data)

def make_disconnection_packet() -> bytes:
    return make_unreliable_packet(PacketType.Disconnection, b"")

def receive_packets(sock: socket.socket, message_size: int) -> Iterable[tuple[tuple[int, int, bytes], tuple[str, int]]]:
    """
    An iterator over socket's received packets. Essentially, it will try to receive as many packets as it can
    until hitting the `BlockingIOError` exception. If a packet is invalid (for example it contains corrupted data) - 
    it will not get returned.
    """

    while True:
        try:
            data, addr = sock.recvfrom(message_size)
            if (packet := open_packet(data)) is not None:
                yield packet, addr
        except BlockingIOError:
            break
        except OSError:
            # This is extremely dangerous, but we'll avoid all OS errors that we'll receive.
            # In particular, we're avoiding the buffer-to-small errors, completely discarding any packets.
            # Overall you can bash me for this, since this is a really stupid solution.
            continue

def packet_sequence_counter(wrap_at: int):
    "A generator that produces packet sequence IDs."

    counter = 1
    while True:
        yield counter
        counter = max(1, (counter+1)%wrap_at)

class Timer:
    "A mini timer for time management"
    def __init__(self, interval: float, is_zero: bool):
        self.interval = interval
        self.on_interval = 0 if is_zero else interval

    def tick(self, dt: float):
        if self.on_interval > 0:
            self.on_interval -= dt

    def has_finished(self):
        return self.on_interval <= 0
    
    def reset(self):
        self.on_interval = self.interval

    def zero(self):
        "Make this clock act immediately. Only usefil in specific cases"
        self.on_interval = 0

class HighUDPConnection:
    BYTES_PER_SECOND = 250_000 # Im being conservative here with 2Mbps or 250KB per second
    PACKETS_PER_SECOND = 200 # This is a pretty high number, so don't judge me! It's only a toy implementation!

    POSSIBLE_SILENCE_DURATION = 10 # It's possible to still have a persistent connection for 10 seconds in case of absense of heartbeat
    HEARTBEAT_RATE = 3.3 # Send a heartbeat every 3.3 seconds

    def __init__(self, sock: socket.socket, to_addr: tuple[str, int], label = ""):
        self.connected_to = to_addr
        self.sock = sock

        self.id_counter = packet_sequence_counter(WRAP_IDS)
        self.received_packets = CircleSet(1000)

        self.acknowledged_packets = CircleSet(1000)
        self.packet_queue: deque[tuple[int, bytes]] = deque()
        """
        This queue stores tuples with this data: (sequence_id, data, addr)
        We store the sequence ID, because all messages that are sent this way are reliable. We don't
        maintain any dictionaries - every message is immediately put at the end of the queue
        when it's time to be sent. IF, however, the ID was already acknowledged in the set - the packet
        gets ignored and doesn't get added to the end anymore.
        """

        self.no_end_heartbeat = Timer(HighUDPConnection.POSSIBLE_SILENCE_DURATION, False)
        "The last packet received from the end-connection (be it heartbeat or any other packet)"

        self.next_self_heartbeat = Timer(HighUDPConnection.HEARTBEAT_RATE, False)

        self.label = label
        "Labels help when debugging"

    def get_addr(self) -> tuple[str, int]:
        "In a connection between address A and B (where A is our socket), this method returns the address of B"
        return self.connected_to
    
    def _queue_message(self, seq_id: int, packet: bytes):
        "Add this message to the queue. An internal method, as it requires ID assignment"
        self.packet_queue.append((seq_id, packet))

    def _send_packet(self, data: bytes):
        # Reset our heartbeat, because we have sent a packet!
        self.next_self_heartbeat.reset()
        self.sock.sendto(data, self.connected_to)

    def disconnect(self):
        "Close this connection by also sending a disconnection packet"

        if self.is_connected():
            self._send_packet(make_disconnection_packet())

        self.no_end_heartbeat.zero()

    def queue_message(self, data: bytes, reliable: bool):
        "This method will both send a message and register it to non-acknowledged dictionary"
        assert len(data) <= BYTES_PER_MESSAGE, f"The message exceeds the {BYTES_PER_MESSAGE} byte limits"

        if reliable:
            new_id = next(self.id_counter)
            packet = make_reliable_packet(new_id, PacketType.Message, data)
        else:
            new_id = 0
            packet = make_unreliable_packet(PacketType.Message, data)

        self._queue_message(new_id, packet)

    def _queue_heartbeat(self):
        self._queue_message(0, make_heartbeat_packet())

    def _get_limits(self, dt: float) -> tuple[int, int]:
        "Computes BPS and PPS limits for the provided delta. If higher than 1 - clamps the results"
        bps, pps = HighUDPConnection.BYTES_PER_SECOND, HighUDPConnection.PACKETS_PER_SECOND
        return (
            min(bps, int(bps * dt)),
            min(pps, int(pps * dt)),
        )

    def _send_queued_messages(self, dt: float):
        """
        The key idea is that we would like to resend our messages as often as possible. This is why we're
        maintaining here a queue. 
        
        If a message already is acknowledged - we will ignore it. In any other case we will 
        both send it and QUEUE AGAIN (so we will come to it a bit later)

        This method can send multiple packets, depending on the amount of time that has passed (delta time).
        Delta time is really important in this calculations, as it allows to 
        """

        allowed_bytes, allowed_packet_amount = self._get_limits(dt)

        # Some packets are large, so we need to ensure to send at least ONE per tick
        at_least_one = True

        # We're swapping these 2 deques, because reliable packets will be added to the end again
        self.packet_queue, packet_queue = deque(), self.packet_queue

        while packet_queue and allowed_packet_amount > 0:
            seq_id, packet = packet_queue.popleft()
            if seq_id in self.acknowledged_packets:
                continue

            packet_size = len(packet)
            if packet_size <= allowed_bytes or at_least_one:
                at_least_one = False
                allowed_bytes -= BASE_UDP_HEADER_SIZE + packet_size
                allowed_packet_amount -= 1

                self._send_packet(packet)

                if seq_id != 0:
                    # If sequence ID isn't zero - we're going to queue it again
                    self._queue_message(seq_id, packet)
            else:
                # We don't have much more bandwidth, so we're putting it back for later
                packet_queue.appendleft((seq_id, packet))
                break
        
        # We need to join them back, as the packet queue might not be entirely consumed
        self.packet_queue = packet_queue+self.packet_queue

    def acknowledge_received_packet(self, seq_id: int):
        "The packet the receiver sent to us was received. This is important to avoid dublicates"
        if seq_id != 0:
            # print(f"{self.label}: Acknowledged {seq_id}, sending this acknowledgement back!")
            self.received_packets.add(seq_id)
            self._queue_message(0, make_acknowledgement_packet(seq_id))
    
    def has_packet_been_received(self, seq_id: int) -> bool:
        "A packet is received if it's ID is not 0 (unreliable), and it its ID is registered in the received database"
        return seq_id in self.received_packets

    def is_connected(self):
        "Returns whether the connection is still active"
        return not self.no_end_heartbeat.has_finished()
    
    def process_packet(self, seq_id: int, ty: PacketType, data: bytes) -> Optional[bytes]:
        "Process a packet, and if it's a message packet - return its bytes"
        ret = None

        self.no_end_heartbeat.reset()

        if ty == PacketType.Acknowledgment:
            if len(data) == 2:
                ack_id = int.from_bytes(data, BYTE_ORDER)
                self.acknowledged_packets.add(ack_id)
                # print(f"{self.label}: Received acknowledgement for {ack_id}")
        elif ty == PacketType.Message:
            if not self.has_packet_been_received(seq_id):
                ret = data
                self.acknowledge_received_packet(seq_id)
        elif ty == PacketType.Disconnection:
            self.no_end_heartbeat.zero()

        return ret

    def tick(self, dt: float):
        self.no_end_heartbeat.tick(dt)
        self.next_self_heartbeat.tick(dt)

        if self.next_self_heartbeat.has_finished():
            self._queue_heartbeat()

        self._send_queued_messages(dt)

class HighUDPConnectionUnstable(HighUDPConnection):
    "Essentially the same as `HighUDPConnection`, but is used when testing unreliable conditions"
    def __init__(self, sock, to_addr, label=""):
        super().__init__(sock, to_addr, label)

    def _send_packet(self, data: bytes):
        for _ in range(2 if should_dublicate() else 1):
            packet_to_send = data
            if should_corrupt():
                packet_to_send = packet_to_send[::-1]

            if not should_lose_packet():
                super()._send_packet(data)

def _maybe_fire(
    callback: Union[None, Callable[[tuple[str, int]], None]], 
    *args 
):
    """
    I know this is silly, but this function is simply here to not call a function if it's `None`.
    This avoid constant `if x is not None` checks.
    """
    if callback is not None:
        callback(*args)

class HighUDPServer:
    "A server is responsible for accepting connections from clients and maintaining their connections"
    def __init__(self, addr: tuple[str, int], max_connections: int):
        self.max_connections = None
        self.set_max_connections(max_connections)

        self.accept_connections = True

        self.connections: dict[tuple[str, int], HighUDPConnection] = {}

        self.sock = make_async_socket(addr, True)
        self.addr = self.sock.getsockname()

        self._connection_cls: HighUDPConnection = HighUDPConnection

        self.recv_queue: deque[bytes, tuple[tuple[str, int]]] = deque()

        self.on_connection: Callable[[tuple[str, int]], None] = None
        "A callback that's fired when a client has connected. A public attribute"
        self.on_disconnection: Callable[[tuple[str, int]], None] = None
        "A callback that's fired when a client has disconnected. A public attribute"

    def get_addr(self) -> tuple[str, int]:
        return self.addr
    
    def set_testing_mode(self, to: bool):
        """
        Change this server to unstable mode. This will only get applied to future connections, and doesn't
        affect existing ones. Setting this to `True` will enable unstable connections.
        """
        self._connection_cls = HighUDPConnectionUnstable if to else HighUDPConnection

    def set_max_connections(self, to: int):
        assert to >= 0, "A number of maximum connections should more than 2"
        self.max_connections = to

    def accept_incoming_connections(self, to: bool):
        "Make this server be able to accept incoming connections. Doesn't affect the existing ones"
        self.accept_connections = to

    def _connection_response(self, addr: tuple[str, int], response: bool):
        assert addr not in self.connections, "Can't overwrite an existing connection"

        if response:
            print("SERVER: Connection accepted for", addr)


            self.connections[addr] = self._connection_cls(self.sock, addr, label="SERVER")
            _maybe_fire(self.on_connection, addr)
        else:
            print("SERVER: Connection refused for", addr)
        
        self.sock.sendto(make_connection_response_packet(response), addr)

    def _process_packet(self, addr: tuple[str, int], seq_id: int, ty: PacketType, data: bytes):
        if addr in self.connections:
            data = self.connections[addr].process_packet(seq_id, ty, data)
            if data is not None:
                # If data is not None - our message is a message packet, thus we can add it to our internal queue
                self.recv_queue.append((data, addr))
        else:
            if ty == PacketType.ConnectionRequest:
                response = self.accept_connections and len(self.connections) < self.max_connections
                self._connection_response(addr, response)

    def has_packets(self) -> bool:
        "Check if the server has any available packets"
        return len(self.recv_queue) > 0
    
    def recv(self) -> tuple[bytes, tuple[str, int]]:
        "Receive a single packet (its address and data). Will panic if the server doesn't have any packets"

        assert self.has_packets(), "Nothing to receive"

        return self.recv_queue.popleft()
    
    def send_to(self, addr: tuple[str, int], data: bytes, reliable: bool):
        if addr in self.connections:
            self.connections[addr].queue_message(data, reliable)

    def broadcast(self, port: int, data: bytes):
        """
        Broadcast provided `data` to all broadcast listeners on the provided `port`.
        Don't confuse this method with sending data to all connected clients - this will actually
        send a broadcast packet to non-clients as well.

        An additional note is that this method doesn't use a direct connection, so when broadcasting - 
        all your packets are going to be sent immediately, since the concept of congestion control
        doesn't get applied here (there's no connection).
        """
        self.sock.sendto(
            make_broadcast_packet(data),
            ("255.255.255.255", port),
        )

    def get_connection_addresses(self) -> tuple[tuple[str, int], ...]:
        return tuple(self.connections.keys())
    
    def has_connection_addr(self, addr: tuple[str, int]) -> bool:
        "Check if the provided address is connected"
        return addr in self.connections
    
    def _remove_connection(self, addr: tuple[str, int], fire_callback: bool):
        """
        Delete the connection under the provided address and create fire the disconnection callback.
        This will panic if the connection isn't present
        """
        del self.connections[addr]
        if fire_callback:
            _maybe_fire(self.on_disconnection, addr)
    
    def disconnect(self, addr: tuple[str, int], fire_callback: bool = True):
        "Disconnect the provided address from the server if it's present"
        
        if self.has_connection_addr(addr):
            self.connections[addr].disconnect()
            self._remove_connection(addr, fire_callback)

    def tick(self, dt: float):
        "Receive as many packets as possible and send your own packets"

        for packet, addr in receive_packets(self.sock, RECV_BYTES):
            self._process_packet(addr, *packet)
        
        # removed_connections = []
        for addr, connection in tuple(self.connections.items()):
            connection.tick(dt)

            # If the connection is closed - we close it as well
            if not connection.is_connected():
                self._remove_connection(addr, True)
            
    def close(self):
        for connection in self.connections.values():
            connection.disconnect()

        self.sock.close()

class HighUDPClient:
    "A client connects to servers"

    class ServerConnector:
        def __init__(self, addr: tuple[str, int], attempts: int, attempts_delay: float):
            self.addr = addr
            self.attempts = attempts
            self.next_attempt = Timer(attempts_delay, True)
        
        def tick(self, dt: float) -> bool:
            "Consumes the connection attempt and returns whether it can continue (`True`) or not (`False`)"

            self.next_attempt.tick(dt)
            retry = False
            if self.next_attempt.has_finished():
                self.next_attempt.reset()
                self.attempts -= 1
                retry = True

            return retry
        
        def is_exhausted(self) -> bool:
            return self.attempts <= 0

    def __init__(self, addr: tuple[str, int]):
        self.connection: HighUDPConnection = None
        self.connection_addr: tuple[str, int] = None

        self.active_connector: HighUDPClient.ServerConnector = None

        self.sock = make_async_socket(addr)
        self.addr = self.sock.getsockname()

        self.recv_queue: deque[bytes] = deque()

        self._connection_cls: HighUDPConnection = HighUDPConnection
        """
        To allow easy unreliable environment testing, the simplest solution was to create a simple
        class placeholder, which can be replaced with an unstable connection class when testing is neccessary.
        
        This is to avoid runtime overhead for normal conditions, while also providing *some* way of testing
        unreliable conditions. Well, a *Pythonic* workaround.
        """

        self.on_connection: Union[None, Callable[[], None]] = None
        "A callback that's fired when the client has connected to the server. A public attribute"
        self.on_disconnection: Union[None, Callable[[], None]] = None
        "A callback that's fired when the client has disconnected from the server. A public attribute"
        self.on_connection_fail: Union[None, Callable[[], None]] = None
        "A callback that's fired when the client fails all attempts to connect to the server. A public attribute"

    def get_addr(self) -> tuple[str, int]:
        return self.addr
    
    def get_server_addr(self) -> Union[tuple[str, int], None]:
        "Return the connected server's address if connected. Else returns `None`"
        return self.connection_addr if self.is_connected() else None

    def set_testing_mode(self, to: bool):
        """
        Change this server to unstable mode. This will only get applied to future connections, and doesn't
        affect existing ones. Setting this to `True` will enable unstable connections.
        """
        self._connection_cls = HighUDPConnectionUnstable if to else HighUDPConnection

    def is_connected(self) -> bool:
        return self.connection is not None and self.connection.is_connected()
    
    def is_trying_to_connect(self) -> bool:
        return self.active_connector is not None
    
    def connect(self, to: tuple[str, int], attempts: int, attempt_delay: float):
        "Start a connection procedure. If a connection is already ongoing - it's going to get overwritten"

        assert not self.is_connected(), "Already is connected"
        self.active_connector = HighUDPClient.ServerConnector(to, attempts, attempt_delay)

    def _continue_connection_establishing(self, dt: float):
        connector = self.active_connector

        retry = connector.tick(dt)
        if retry:
            try:
                self.sock.sendto(
                    make_connection_request_packet(),
                    connector.addr
                )
            except OSError:
                # If we catch an OS error - we abort. There's a chance we're sending packets
                # to an incorrect address
                connector.attempts = 0
        
        if connector.is_exhausted():
            _maybe_fire(self.on_connection_fail)
            self.active_connector = None

    def _process_packet(self, seq_id: int, ty: PacketType, data: bytes):
        if self.connection is not None:
            data = self.connection.process_packet(seq_id, ty, data)
            if data is not None:
                self.recv_queue.append(data)
        elif self.active_connector is not None:
            # ConnectionResponse only contains a single byte of data, which is True/False
            if ty == PacketType.ConnectionResponse:
                if data and data[0] == True:
                    print("CLIENT: Connected to", self.active_connector.addr)
                    # Move to an active UDP connection
                    self.connection_addr = self.active_connector.addr
                    self.connection = self._connection_cls(self.sock, self.connection_addr, label="CLIENT")
                    _maybe_fire(self.on_connection)
                else:
                    _maybe_fire(self.on_connection_fail)

                # Remove this connector
                self.active_connector = None
                    
    def has_packets(self) -> bool:
        "Check if the client has any available packets"
        return len(self.recv_queue) > 0
    
    def recv(self) -> bytes:
        "Receive a single packet (its data). Will panic if the client doesn't have any packets"

        assert self.has_packets(), "Nothing to receive"

        return self.recv_queue.popleft()
    
    def send(self, data: bytes, reliable: bool):
        if self.connection is not None:
            self.connection.queue_message(data, reliable)

    def _remove_connection(self, fire_callback: bool):
        "Remove the connection and optionally fire the binded callback"
        self.connection = None
        self.connection_addr = None

        if fire_callback:
            _maybe_fire(self.on_disconnection)

    def disconnect(self, fire_callback: bool = True):
        "Disconnect from the currently connected server"

        if self.is_connected():
            self.connection.disconnect()
            self._remove_connection(fire_callback)

    def tick(self, dt: float):
        "Receive as many packets as possible and send your own packets"

        for packet, addr in receive_packets(self.sock, RECV_BYTES):
            # It should be either the server or a connector address
            if addr == self.connection_addr or (self.active_connector and self.active_connector.addr == addr):
                self._process_packet(*packet)
        
        if self.is_trying_to_connect():
            self._continue_connection_establishing(dt)
        elif self.is_connected():
            self.connection.tick(dt)
        elif self.connection:
            # If there's no connection, but we still have a connection object - remove it
            self._remove_connection(True)

    def close(self):
        if self.is_connected():
            self.connection.disconnect()

        self.sock.close()
        
class BroadcastListener:
    """
    Broadcast listener is an abstraction that allows you to listen for broadcasted messages. 
    Why not just use the Client to receive broadcasts? Well, I think the problem with this API is that
    a client is always expected to have the same port. Something that isn't possible 
    """
    def __init__(self, addr: tuple[str, int]):
        # We're using a shared socket here, because it makes it possible to use the same port for
        # multiple broadcast listeners accross multiple Python sessions. This is highly useful for
        # testing.
        self.sock = make_async_socket(addr, shared=True)
        self.recv_queue: deque[tuple[bytes, tuple[str, int]]] = deque()
    
    def fetch(self):
        "Fetch for any new packets on this listener. Fetching will allow you to later get your packets using the `recv` method"
        for (_, ty, data), addr in receive_packets(self.sock, BYTES_PER_MESSAGE):
            if ty == PacketType.Broadcast:
                self.recv_queue.append((data, addr))

    def has_packets(self) -> bool:
        "Check if the listener has any available packets"
        return len(self.recv_queue) > 0
    
    def recv(self) -> tuple[bytes, tuple[str, int]]:
        "Receive a single packet (its data and address). Will panic if the listener doesn't have any packets"

        assert self.has_packets(), "Nothing to receive"

        return self.recv_queue.popleft()

    def close(self):
        "Close this broadcast listener"
        self.sock.close()
        