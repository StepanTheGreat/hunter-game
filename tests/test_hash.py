from ward import test
from core.network.fnv import fnv1_hash, hash_data, unhash_data

@test("Test FNV1 hash function")
def _():
    data = b"hello"

    assert fnv1_hash(data) == fnv1_hash(b"hello")
    
    data = data + b"!"

    assert fnv1_hash(data) != fnv1_hash(b"hello")

@test("Check data signatures")
def _():
    data = b"hello"

    hashed_data = hash_data(data)
    assert unhash_data(hashed_data) == data

    hashed_data = hashed_data + b"!"
    assert unhash_data(hashed_data) is None