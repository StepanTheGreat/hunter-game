""" A tiny module for general file loading """

from os.path import abspath
import sys

from json import loads as json_loads
from jsonschema import validate, ValidationError

if getattr(sys, "frozen", False):
    PROJECT_DIR = sys._MEIPASS + "/"
else:
    PROJECT_DIR = abspath(__file__ + "/../../") + "/"

# To explain this monstrosity... We would like to support 2 ways of executing our game - via python,
# and via pyinstaller binaries. In case of python, our execution directory can be different from the
# one where `main.py` is located, thus relying on relative paths like for assets or configs is just
# impossible. Using this strange `abspath(__file__ + "/../../")` we're essentially saying that taking
# the file path of this `file.py` location, we would like to go 2 directories back, and set it as our
# project directory.
#
# For the pyinstaller thing, pyinstaller in the bundled python runtime sets a special attribute in the
# `sys` package called `frozen`, which means that the app is running as an executable. Pyinstaller
# allows us to bundle everything (even our assets) into a SINGLE executable file, which is EXTREMELY
# convenient for project sharing. It does so by unbundling everything at runtime in a temporary
# OS folder before executing our app. `_MEIPASS` is that exact directory, which we will use if
# we're running a frozen application


def localize_path(path: str):
    "Join an arbitrary path from the project directory"
    return PROJECT_DIR + path

def load_file_str(path: str) -> str:
    "Load a file as a string"
    contents = None
    with open(path, "r") as file:
        contents = file.read()
    return contents

def load_json_and_validate(path: str, schema: dict) -> dict:
    """
    Load and automatically validate the file at the provided path against given schema.
    If the file passes - this function returns the resulting object, but if it doesn't, it's
    going to raise a validation error with some additional details
    """

    obj = json_loads(load_file_str(path))

    try:    
        validate(obj, schema)
    except ValidationError as e:
        print(f"File at {path} failed JSON schema validation:")
        raise e

    return obj

def load_file_bytes(path: str) -> bytes:
    "Load a file as a byte array"
    contents = None
    with open(path, "rb") as file:
        contents = file.read()
    return contents

def get_file_dir(path: str) -> str:
    "Convert the absolute file path to a directory path relative to the file"

    return abspath(path + "/../")+"/"