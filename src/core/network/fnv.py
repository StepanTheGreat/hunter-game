from typing import Optional

FNV_PRIME = 0x100000001B3
FNV_OFFSET =  0xCBF29CE484222325

def fnv1_hash(data: bytes) -> int: 
    "This is a Fowler-Noll-Vo quick hash function which returns 4-byte hash integers "
    ret_hash = FNV_OFFSET
    for byte in data:
        ret_hash = ((ret_hash * FNV_PRIME) ^ byte) & 0xFFFFFFFF

    return ret_hash 

def unhash_data(b: bytes) -> Optional[bytes]:
    "Check if the data signature is correct, and if so - returns the original data (without the hash)"

    if len(b) < 4:
        # Hashed data has to be at least 4 bytes long
        return

    data = b[4:]
    data_hash = int.from_bytes(b[:4], "big")

    if data_hash == fnv1_hash(data):
        return data
    
    # Else the hashes don't collide
    
def hash_data(data: bytes) -> bytes:
    """
    Hash these bytes and add the hash signature at the start. 
    If you would like to check it later - use the `unhash_data` function
    """
    data_hash = fnv1_hash(data)
    data_hash = data_hash.to_bytes(4, "big")

    return data_hash + data