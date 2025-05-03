from ward import test, raises
import struct

from plugin import Resources

from plugins.shared.network import rpc, rpc_raw, RPCFormatError, is_rpc_reliable

RESOURCES = Resources()
# We're mocking resources here since we don't really care about them when testing RPCs

@test("Test RPC function calling")
def _():

    # We're going to create this 1-value list to create a reference
    result = [None]

    # Let's create an RPC that expects 2 integers as input
    @rpc("ii")
    def add_values(_, a, b):
        result[0] = a+b

    # Our RPC has a method which makes it easy to convert Python arguments into bytes, which makes it simple
    # to call the underlying RPC
    add_values(
        RESOURCES,
        add_values.serialize_call(5, 5)
    )

    # We should get our proper result
    assert result[0] == 10

    # Using an incorrect format when serializing will throw a `struct` Exception.
    with raises(struct.error):
        add_values.serialize_call(1)

    # Using incorrect byte arguments with the RPC however, will throw an `RPCFormatError` exception
    with raises(RPCFormatError):
        add_values(RESOURCES, b"abc")
        # Expected 8 bytes, but received only 3

@test("Test raw RPCs")
def _():

    result = []

    # A raw RPC is a direct RPC for struct optimisations. No checks are performed on it, meaning that
    # even 0 bytes would pass by fine.
    @rpc_raw
    def push_result(_, data: bytes):
        result.append(data)

    values = [b"a", b"bb", b""]

    for value in values:
        push_result(RESOURCES, value)

    # As we can see, it doesn't care about anything
    assert result == values

    # So does its serialize method. It only exists for API's consistence

    for value in values:
        push_result.serialize_call(value)

@test("RPCs should have unique IDs")
def _():
    @rpc_raw
    def a(_, data: bytes):
        ...

    @rpc("")
    def b(_):
        ...

    @rpc("")
    def c(_):
        ...

    assert a.__rpc_id != b.__rpc_id
    assert b.__rpc_id != c.__rpc_id
    assert c.__rpc_id != a.__rpc_id

@test("Test RPC reliability decorator")
def _():
    @rpc_raw(reliable=True)
    def raw_reliable():
        pass

    @rpc_raw
    def raw_unreliable():
        pass

    @rpc_raw()
    def raw_unreliable2():
        pass

    assert is_rpc_reliable(raw_reliable)
    assert not is_rpc_reliable(raw_unreliable)
    assert not is_rpc_reliable(raw_unreliable2)

    @rpc("")
    def unreliable():
        pass

    @rpc("", reliable=True)
    def reliable():
        pass

    assert is_rpc_reliable(reliable)
    assert not is_rpc_reliable(unreliable)