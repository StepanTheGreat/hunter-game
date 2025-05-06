from ward import test
from modules.network import *

DT = 1/60
IP = "127.0.0.1"

ADDR_SERVER = (IP, 1500)
ADDR_CLIENT = (IP, 1501)

ADDR_CLIENT2 = (IP, 1502)
ADDR_CLIENT3 = (IP, 1503)

PORT_BROADCAST = 1567
ADDR_BROADCAST = ("0.0.0.0", PORT_BROADCAST) # On linux, broadcasts can't be received on localhost

ADDR_SERVER_DUMMY = (IP, 1499)
"This address doesn't contain anything"

def make_test_pair() -> tuple[HighUDPServer, HighUDPClient]:
    "-1% of boilerplate!"
    return HighUDPServer(ADDR_SERVER, 4), HighUDPClient(ADDR_CLIENT)

def connect_actors(server: HighUDPServer, *clients: HighUDPClient):
    for client in clients:
        client.connect(server.addr, 2, DT)
        tick_actors(0, client, server, client)

def tick_actors(dt: float, *actors, times: int = 1):
    for _ in range(times):
        for actor in actors:
            actor.tick(dt)

def fetch_listeners(*listeners: BroadcastListener):
    for listener in listeners:
        listener.fetch()

def close_actors(*actors):
    "Close sockets of the provided actors (client or server)"
    for actor in actors:
        actor.close()

@test("Test basic server/client connections")
def _():
    # Create our server and client
    server, client = make_test_pair()
    connect_actors(server, client)

    assert client.is_connected()
    assert server.connections[ADDR_CLIENT]

    close_actors(server, client)

@test("Test heartbeat")
def _():
    # Create our server and client
    server, client = make_test_pair()
    connect_actors(server, client)

    # Now, for the client to become disconnected, it should not send any heartbeats/messages in 10 seconds
    tick_actors(10, client, server)

    # They both now should be disconnected
    assert not server.has_connection_addr(ADDR_CLIENT)
    assert not client.is_connected()

    # Let's reconnect them again
    connect_actors(server, client)

    # Tick them CLOSE to the heartbeat limit
    tick_actors(9.99, client, server)

    # They should still be connected
    assert server.has_connection_addr(ADDR_CLIENT)
    assert client.is_connected()

    # Now, for shorter durations of time, they should automatically send heartbeats
    tick_actors(5, client, server, times=5)

    # Even though in sum 25 seconds have passed - they still are connected
    assert server.has_connection_addr(ADDR_CLIENT)
    assert client.is_connected()

    close_actors(server, client)

@test("Test data exchange")
def _():
    server, client = make_test_pair()

    # When not connected, they shouldn't have any packets available
    assert not server.has_packets()
    assert not client.has_packets()

    # Connect them
    connect_actors(server, client)

    # Let's send a simple hello
    client.send(b"hello", True)

    # The order in which we tick here is important: first we let the client leave its QUEUE and THEN
    # We're also using 1 here, since the amount of bytes/packets an actor can send is bound to delta time
    # to avoid congestion. 1 is the maximum number, so it simply means it will use our entire limits
    tick_actors(1, client, server)

    # After ticking, we should have a packet from the server
    assert server.has_packets()

    # We should get the same IP address and data that we sent
    assert server.recv() == (b"hello", ADDR_CLIENT)

    # That should be it however
    assert not server.has_packets()

    #
    # Let's try the other way now, but with more packets
    #

    # This is a good use of our bandwidth
    messages = (b"hello", b" ", b"again")

    # Let's send those to our client
    for msg in messages:
        server.send_to(ADDR_CLIENT, msg, True)

    # We're swapping the order, as server now needs to send first
    tick_actors(1, server, client)

    # Assert that all messages were received and are correct
    for msg in messages:
        assert client.recv() == msg

    assert not client.has_packets()

    close_actors(server, client)


@test("Test continuos packet sending/receiving")
def _():
    server, client = make_test_pair()
    connect_actors(server, client)

    # In this test we're going to simply simulate 100 packets send both to client and server
    # We should see ZERO dublicates

    for i in range(100):
        # We take a number and convert it into bytes
        data = i.to_bytes(2, "big")

        # Send it to the client
        server.send_to(ADDR_CLIENT, data, True)

        client.send(data, True)

        # Update both actors
        tick_actors(DT, server, client, server)

        # Receive the data and assert that it is correct
        assert client.recv() == data
        assert server.recv() == (data, ADDR_CLIENT)

    close_actors(server, client)

@test("Test server closing/opening incoming connections")
def _():
    server, client = make_test_pair()
    client2 = HighUDPClient(ADDR_CLIENT2)

    # In this test we're going to need an another client - client 2!
    # We'll set a maximum limit of 2, thus the server wouldn't accept client 2's request. What a tragedy!

    server.set_max_connections(1)
    connect_actors(server, client, client2)

    # The client 1 should be connected
    assert client.is_connected()
    assert server.has_connection_addr(ADDR_CLIENT)

    # But not client 2
    assert not client2.is_connected()
    assert not server.has_connection_addr(ADDR_CLIENT2)

    # Great, now let's let him finally connect
    server.set_max_connections(4)
    connect_actors(server, client2)

    assert client2.is_connected()
    assert server.has_connection_addr(ADDR_CLIENT2)

    # But this time, we're going to lock the server up
    server.accept_incoming_connections(False)

    # And try to connect from client3!
    client3 = HighUDPClient(ADDR_CLIENT3)
    connect_actors(server, client3)

    # Shouldn't be able to
    assert not client3.is_connected()
    assert not server.has_connection_addr(ADDR_CLIENT3)

    # Now, if one of our clients DOES disconnect
    client.disconnect()
    assert not client.is_connected()

    tick_actors(DT, server, client, client2)
    
    # They shouldn't be present on the server
    assert not server.has_connection_addr(ADDR_CLIENT)

    connect_actors(server, client)

    # Yet, we wouldn't be able to reconnect them back either, because it's still locked up!

    assert not client.is_connected()
    assert not server.has_connection_addr(ADDR_CLIENT)

    close_actors(server, client, client2, client3)

@test("Test reliable delivery in unreliable environment")
def _():
    # Now it's spooky time. We're going to play in an unstable, random environment

    server, client = make_test_pair()

    # To enable unstable environment, we're going to set testing mode True on both the server
    # and client
    server.set_testing_mode(True)
    client.set_testing_mode(True)

    connect_actors(server, client)

    # Let's first enable corruption, so our packets can actually get corrupted. (This simply reverses them)
    set_corruption_rate(0.75)

    # Send our message using reliable channel. We aren't testing unreliable channels, because... they're unreliable.
    message = b"hello"
    client.send(message, True)

    # Now, we're going to tick 16 times. This test is highly random, so that's okay if it sometimes fail - 
    # but usually 16 is a safe number.

    print("-- First test")
    tick_actors(DT, server, client, times=16)
    
    # We should receive our message as it is
    assert server.recv() == (message, ADDR_CLIENT)
    assert not server.has_packets() # Without anything else


    # Now let's play with dublicates. 10% should be good enough
    set_dublicates_rate(0.5)

    # We send a message from our server to the client
    server.send_to(ADDR_CLIENT, message, True)

    # Again, tick 16 times
    print("-- Second test")
    tick_actors(DT, server, client, times=16)
    
    # And of course, make sure that we only receive one message, and that this message is fully intact
    assert client.recv() == message
    assert not client.has_packets()

    # Now it's time to play with fire. We're going to set our loss-rate to 5%, and reduce other options
    # (since it would be impossible to deliever otherwise)
    set_loss_rate(0.05)
    set_corruption_rate(0.05)
    set_dublicates_rate(0.1)

    # We're going to send 2 messages here, from both sides

    message_client = b"My name's Brian"
    message_server = b"My name's Jeff"

    server.send_to(ADDR_CLIENT, message_server, True)
    client.send(message_client, True)
    
    # Tick them againy
    print("-- Third test")
    tick_actors(DT, server, client, times=16)

    # They should now all interchange their messages
    assert server.recv() == (message_client, ADDR_CLIENT)
    assert client.recv() == message_server

    # And these should be their only packets
    assert not server.has_packets()
    assert not client.has_packets()

    reset_unreliability()
    close_actors(server, client)

@test("Test unreliable packets")
def _():
    server, client = make_test_pair()
    connect_actors(server, client)

    # So far we have only tested reliable packets, but it's important to also check that unreliable
    # packets work as well

    message_client = b"hello"
    message_server = b"welcome"

    client.send(message_client, False)
    server.send_to(ADDR_CLIENT, message_server, False)

    # Let them exchange messages
    tick_actors(DT, server, client, times=2)

    assert client.recv() == message_server
    assert server.recv() == (message_client, ADDR_CLIENT)

    assert not client.has_packets() and not server.has_packets()

    # All works great. Now, let's use them in conjuction with reliable packets

    # We're going to send these packets
    messages = (b"now", b"I", b"know", b"my", b"a", b"b", b"c", b"'s")
    reliable = False

    for message in messages:
        client.send(message, reliable)
        server.send_to(ADDR_CLIENT, message, reliable)

        # Invert this variable every time
        reliable = not reliable

    # Lets tick them. Even though in our connection multiple packets can be sent in a single tick -
    # for simplicity, we're going to tick the same amount of times as there are messages.
    tick_actors(DT, server, client, times=len(messages))

    for message in messages:
        assert client.recv() == message
        assert server.recv() == (message, ADDR_CLIENT)
    
    assert not client.has_packets() and not server.has_packets()

    close_actors(server, client)

@test("Test packet batching")
def _():
    server, client = make_test_pair()
    connect_actors(server, client)

    # Multiple packets can be batched in a single tick. This tests asserts that we can send multiple packets
    # in a single tick.

    # In our defined constant, we should be able to send up to 250K bytes per second or 200 packets per second.
    # These limits exist because while we could measure everything in the a amount of bytes transfered every second 
    # - we should also account for the amount of packets, because they're as well processed by the software.
    # In our constants, we can send up to 4KB or 3 packets per tick (60 tps).
    # 
    # But, there is also fragmentation issues, which this library avoids entirely by... not allowing you to
    # send more than 1024 bytes per message... I know, right?
    # 
    # So, what we're going to do, is construct 3 well designed packets, so that they will all be able to 
    # fit in a single tick.

    # This message is exactly 1024 bytes long
    long_message = b"long"*256

    # Queue our 3 long messages
    for _ in range(3):
        client.send(long_message, False)

    # Tick them EXACTLY once, with client being the first
    tick_actors(DT, client, server, times=1)

    # Receive all 4 messages in their totality
    for _ in range(3):
        assert server.recv() == (long_message, ADDR_CLIENT)
    assert not server.has_packets()

    close_actors(server, client)

@test("Test multiple clients")
def _():
    server, client = make_test_pair()
    client2 = HighUDPClient(ADDR_CLIENT2)

    connect_actors(server, client, client2)

    # This test is pretty straightforward - if everyone properly receives all messages

    server.send_to(ADDR_CLIENT2, b"hi", True)

    tick_actors(DT, server, client, client2)

    assert client2.recv() == b"hi"

    assert not client.has_packets()
    assert not client2.has_packets()

    message1 = b"I'm first"
    message2 = b"No, I'm first!"

    client.send(message1, True)
    client2.send(message2, True)

    tick_actors(DT, client, client2, server)

    for (message, addr) in ((message1, ADDR_CLIENT), (message2, ADDR_CLIENT2)):
        assert server.recv() == (message, addr)
    assert not server.has_packets()

@test("Use actual socket addresses that are picked up when binding sockets")
def _():
    # We would like to use automatic OS address binding. For example, we don't know any available port,
    # so we're going to put 0 instead
    auto_addr = ("127.0.0.1", 0)

    client = HighUDPClient(auto_addr)
    server = HighUDPServer(auto_addr, 1)

    # When bound however, they should have a different port from the one we gave
    assert client.get_addr() != auto_addr
    assert server.get_addr() != auto_addr
    assert client.get_addr() != server.get_addr()

@test("Test broadcasters")
def _():
    server, client = make_test_pair()

    # We're going to create 2 listeners, and they should be able to perfectly coexist
    listener1 = BroadcastListener(ADDR_BROADCAST)
    listener2 = BroadcastListener(ADDR_BROADCAST)

    message = b"hello"

    # A broadcast is a special method, because it sends packets immediately, without us
    # needing to tick the server
    server.broadcast(PORT_BROADCAST, message)

    # We always need to manually fetch all packets on listeners
    fetch_listeners(listener1, listener2)

    # Now, we only should receive a single packet
    for listener in (listener1, listener2):
        assert listener.recv() == (message, ADDR_SERVER)
        assert not listener.has_packets()

    # Our client on the other hand, not being connected to anything - shouldn't receive anything
    client.tick(DT)
    assert not client.has_packets()

    close_actors(server, client, listener1, listener2)

@test("Test immediate disconnection")
def _():
    server, client = make_test_pair()
    connect_actors(server, client)

    # We're going to disconnect them using special `disconnect` method, that also is going to send
    # a disconnection packet
    client.disconnect()
    tick_actors(DT, server, client)

    # This packets has a high chance of immediately terminating the connection in 1 tick!

    assert not server.has_connection_addr(ADDR_CLIENT)
    assert not client.is_connected()


    # Now let's do the same thing, but the other way around
    connect_actors(server, client)
    
    # Again, the connection is terminated in a single tick!
    server.disconnect(ADDR_CLIENT)
    tick_actors(DT, server, client)

    assert not server.has_connection_addr(ADDR_CLIENT)
    assert not client.is_connected()

    close_actors(server, client)

@test("Test connection hooks for connection/disconnection/connection failure")
def _():
    server, client = make_test_pair()

    def clear_all(*lists: list):
        for lst in lists:
            lst.clear()

    def are_empty(*lists: list) -> bool:
        return all(len(lst) == 0 for lst in lists)

    # This is an ugly way of doing this, but lambdas don't really support statements
    server_connections = []
    server_disconnections = []

    server.on_connection = lambda _: server_connections.append(1)
    server.on_disconnection = lambda _: server_disconnections.append(1)

    # Now for the client

    client_connections = []
    client_disconnections = []
    client_fails = []

    client.on_connection = lambda: client_connections.append(1)
    client.on_disconnection = lambda: client_disconnections.append(1)
    client.on_connection_fail = lambda: client_fails.append(1)

    # Let's first tick them

    tick_actors(DT, server, client)

    # Obviously, they should produce ANY events when nothing has happened
    assert are_empty(
        server_connections, server_disconnections, 
        client_connections, client_disconnections, client_fails
    )
    
    # Let's connect them
    connect_actors(server, client)

    # They both should produce connection events
    assert not are_empty(server_connections, client_connections)

    # We clear again, but this time we're going to wait them out until they disconnect from heartbeat
    clear_all(server_connections, client_connections)

    # Tick them exactly 10 seconds
    tick_actors(10, server, client)

    # They should produce disconnection events
    assert not are_empty(server_disconnections, client_disconnections)
    clear_all(server_disconnections, client_disconnections)


    # Now, let's try the same, but with direct disconnections

    connect_actors(server, client)
    clear_all(server_connections, client_connections)

    # Let's disconnect our client and see the result
    client.disconnect()
    tick_actors(DT, server, client)
    assert client_disconnections
    assert server_disconnections
    clear_all(server_disconnections, client_disconnections)

    # Connect them back
    connect_actors(server, client)
    clear_all(server_connections, client_connections)

    # Re-do the same, but from the server
    server.disconnect(ADDR_CLIENT)
    tick_actors(DT, server, client)
    assert not are_empty(server_disconnections, client_disconnections)

    clear_all(server_connections, client_connections)

    # Now, let's check connection failures

    server.accept_incoming_connections(False)
    connect_actors(server, client)

    # This should fail
    assert client_fails
    client_fails.clear()

    # Now we're going to instead connect our client, but only tick them, without the server.
    # This is for us to be able to see if it will call our function in case of exhaustion of all attempts

    client.connect(ADDR_SERVER_DUMMY, 4, DT)
    [client.tick(DT) for _ in range(5)]

    # The client should now exhaust all its attempts and call the function
    assert client_fails 

    # Finally, we have an option to disable or overwrite hooks
    client.on_connection = None

    # Clear and connect them again
    clear_all(server_connections, client_connections)
    server.accept_incoming_connections(True)
    connect_actors(server, client)

    assert server_connections
    assert not client_connections

    close_actors(server, client)