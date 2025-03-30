""" A tiny module for general file loading """

SRC_PATH = __file__ + "/../"
"""
This is an ugly way of solving it, but since `file.py` is in the same path as `main.py`,
we can take this absolute path, go back to `src` using `..`, then finally move to any other local 
file we want without worrying about the directory from which the user has run our app.
"""

def src_dir(path: str):
    "Join an arbitrary path from the source directory"
    return SRC_PATH + path

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