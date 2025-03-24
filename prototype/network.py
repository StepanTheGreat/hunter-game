from pygame.time import Clock
from typing import Optional, Any

from collections import deque

from enum import Enum, auto

import socket
import random as rnd
from sys import argv

DELAY_TIME = 1
FPS = 60
MESSAGE_SIZE = 256
IS_SENDER =  "--sender" in argv

class CircleSet:
    """
    The idea behind a circle set is that its keys aren't permanent. They're added to a queue, where 
    when a limit is reached - the first key that was added to the set will be removed from the set.
    """
    def __init__(self, size: int):
        self.set = set()
        self.queue = deque()
        self.size = size

    def add(self, value: Any):
        "Add a new value to this recyclable set"
        self.queue.append(value)
        if len(self.queue) > self.size:
            self.set.remove(self.queue.popleft())

        self.set.add(value)

    def __contains__(self, value: Any):
        return value in self.queue
    
    def __len__(self) -> int:
        return len(self.set)

def fnv1_hash(data: bytes) -> int: 
    "This is a Fowler-Noll-Vo hash function"
    FNV_PRIME = 0x100000001B3
    FNV_OFFSET =  0xCBF29CE484222325

    ret_hash = FNV_OFFSET
    for byte in data:
        ret_hash = ((ret_hash * FNV_PRIME) ^ byte) & 0xFFFFFFFF

    return ret_hash 

class PacketType(Enum):
    Acknowledgment = auto()
    "A packet has been acknowledged"
    Message = auto()
    "This is simply a data packet"

def open_packet(b: bytes) -> Optional[tuple[int, int, bytes]]:
    assert len(b) >= 4+2+1, "[hash][hash][hash][hash][seq][seq][ty]...[data], not enough bytes!"

    data = b[4:]
    message_hash = int.from_bytes(b[:4], "little")
    message_id = int.from_bytes(data[:2], "little")
    message_ty = b[2]
    
    required_hash = fnv1_hash(data)
    if message_hash == required_hash:
        return message_id, message_ty, data[3:]
    
    # Else the hashes don't collide
    
def make_packet(id: int, ty: int, data: bytes) -> bytes:
    packet_id = id.to_bytes(2, "little")
    packet_ty = ty.to_bytes(1, "little")

    packet = packet_id + packet_ty + data
    packet_hash = fnv1_hash(packet)
    packet_hash = packet_hash.to_bytes(4, "little")

    return packet_hash + packet

# The concept of a broadcaster and a high-level UDP socket should be separate.
# A broadcaster doesn't receive any data and doesn't care abour reliability (except for data integrity)

class HighUDP:
    SEQUENCE_ID_LIMIT = 2**16
    RESEND_FLOW = 1/10

    "A high-level UDP socket"
    def __init__(self, addr: tuple[str, int], broadcasting: bool = False):
        self.received_packets = CircleSet(2**16)
        self.next_sequence_id = 0

        self.resend_timer = 0

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.sock.bind(addr)

        self.recv_chance = 0
        self.dublicate_chance = 0
        # This is not how it works essentially, but it's a simple way to basically break data into nothing
        self.shuffling_chance = 0

        self.broadcasting = broadcasting
        if self.broadcasting:
            self.sock.setsockopt(socket.SOL_SOCKET,  socket.SO_BROADCAST, 1)

    def __get_sequence_id(self) -> int:
        """
        Automatically increment the internal sequence id and return a new one.
        If a limit of SEQUENCE_ID_LIMIT is reached - overflows back to zero
        """
        next_id = self.next_sequence_id
        self.next_sequence_id = (self.next_sequence_id + 1) % HighUDP.SEQUENCE_ID_LIMIT

        return next_id

    def broadcast(self, message: bytes, port: int):
        assert self.broadcasting, "Can't broadcast on a non-broadcasting socket!"
        self.sendto(message, ("255.255.255.255", port))

    def update(self, dt: float):
        self.resend_timer -= dt

        if

    def sendto(self, message: bytes, to: tuple[str, int]):
        "Send a datagram to an address"

        message_id = self.__get_sequence_id()
        message = make_packet(message_id, 0, message)
        print("Sending: ", message)
        
        if self.shuffling_chance and rnd.randint(0, self.shuffling_chance) != 0:
            # Data was received... in an interesting state...
            message = list(message)
            rnd.shuffle(message)
            message = bytes(message)

        self.sock.sendto(message, to)

        if self.dublicate_chance and rnd.randint(0, self.dublicate_chance) != 0:
            # Send a dublicate
            self.sock.sendto(message, to)
    
    def recv(self, amount: int) -> Optional[tuple[bytes, tuple]]:
        "Either receive an entire datagram, or `None`"
        
        try:
            data, addr = self.sock.recvfrom(amount)
            unpacked = open_packet(data)

            if self.recv_chance and rnd.randint(0, self.recv_chance) != 0:
                print("Failed to receive")
                # Unreliable network, couldn't send
                return

            if unpacked is not None:
                m_id, m_ty, m_data = unpacked
                if m_id not in self.received_packets:
                    self.received_packets.add(m_id)
                    return m_data, addr
                else:
                    print("Got a dublicate")
            else:
                print("Got a tampered packet")
        except BlockingIOError:
            return None


def main():
    clock = Clock()

    # Create a UDP socket and bind it to local network at port 8888
    high_sock = HighUDP(("localhost", 0 if IS_SENDER else 8888), True)

    high_sock.dublicate_chance = 1
    high_sock.shuffling_chance = 1
    high_sock.recv_chance = 0

    # Enable broadcast messages

    next_message = 0
    i = 0
    while 1:
        dt = clock.tick(FPS) / 1000

        if IS_SENDER:
            next_message -= dt
            if next_message < 0:
                i = (i + 1) % 100 
                next_message = DELAY_TIME
                msg = f"Hi there {i}"
                high_sock.broadcast(msg.encode("UTF-8"), 8888)

        else:
            packet = high_sock.recv(256)
            if packet is not None:
                bi, addr = packet
                try:
                    print(bi.decode("UTF-8"))
                except UnicodeDecodeError:
                    print("Failed to decode the message")

if __name__ == "__main__":
    main()