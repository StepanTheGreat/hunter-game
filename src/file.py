# A tiny module for general file loading 

def load_file_str(path: str) -> str:
    "Load a file as a string"
    contents = None
    with open(path, "r") as file:
        contents = file.read()
    return contents

def load_file_bytes(path: str) -> bytes:
    "Load a file as a byte array"
    contents = None
    with open(path, "rb") as file:
        contents = file.read()
    return contents