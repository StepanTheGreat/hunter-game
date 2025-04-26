from ward import test, raises
import struct

from plugins.network import rpc, rpc_raw, RPCFormatError

@test("Test RPC function calling")
def _():

    # We're going to create this 1-value list to create a reference
    result = [None]

    # Let's create an RPC that expects 2 integers as input
    @rpc("ii")
    def add_values(a, b):
        result[0] = a+b

    # Our RPC has a method which makes it easy to convert Python arguments into bytes, which makes it simple
    # to call the underlying RPC
    add_values(
        add_values.serialize_call(5, 5)
    )

    # We should get our proper result
    assert result[0] == 10

    # Using an incorrect format when serializing will throw a `struct` Exception.
    with raises(struct.error):
        add_values.serialize_call(1)

    # Using incorrect byte arguments with the RPC however, will throw an `RPCFormatError` exception
    with raises(RPCFormatError):
        add_values(b"abc")
        # Expected 8 bytes, but received only 3

@test("Test raw RPCs")
def _():

    result = []

    # A raw RPC is a direct RPC for struct optimisations. No checks are performed on it, meaning that
    # even 0 bytes would pass by fine.
    @rpc_raw
    def push_result(data: bytes):
        result.append(data)

    values = [b"a", b"bb", b""]

    for value in values:
        push_result(value)

    # As we can see, it doesn't care about anything
    assert result == values

    # So does its serialize method. It only exists for API's consistence

    for value in values:
        push_result.serialize_call(value)

@test("RPCs should have unique IDs")
def _():
    @rpc_raw
    def a(data: bytes):
        ...

    @rpc("")
    def b():
        ...

    @rpc("")
    def c():
        ...

    assert a.__rpc_id != b.__rpc_id
    assert b.__rpc_id != c.__rpc_id
    assert c.__rpc_id != a.__rpc_id


    