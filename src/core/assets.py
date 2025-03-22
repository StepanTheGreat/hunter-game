from typing import TypeVar, Callable
from plugin import Resources, Plugin, Schedule

from main import AppConfig

# File contents
C = TypeVar("C", str, bytes)

def load_file(path: str, ret: C) -> C:
    "Load a file and return its contents in a provided type. Supported modes are str and bytes"
    contents = None
    mode = "rb" if ret == bytes else "r" 
    with open(path, mode) as file:
        contents = file.read()
    return contents

# Asset
A = TypeVar("A")

class AssetManager:
    "An asset manager is an asster storage, loader and cache at the same time"
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir
        self.database: dict[type, dict[str, object]] = {}
        "A database groups assets by their type. Each group is also a small database, but this time of their names"

        self.loaders: dict[type, Callable[[str]]] = {}
        """
        A database of loaders. An asset type has to first have a registered load function. 
        In any other case, an asset manager doesn't know how to load assets
        """

    def add_loader(self, ty: A, f: Callable[[A, str], A]):
        "Add an asset loader function for the provided asset type"
        self.loaders[ty] = f

    def load(self, ty: A, path: str) -> A:
        assert ty in self.loaders, "The requested asset type doesn't have a loader"
        
        # If we're able to get this asset from our database, we will return it early.
        # First check if the type exists
        # Then check if said group has an asset
        if (ty_group := self.database.get(ty)) is not None:
            if (asset := ty_group.get(path)) is not None:
                return asset

        # Load the asset using the registered loader function
        loaded_asset = self.loaders[ty](self.assets_dir+path)

        # Initialize a new type map if it doesn't exist
        if ty not in self.database:
            self.database[ty] = {}

        # Store this asset for future use
        self.database[ty][path] = loaded_asset

        return loaded_asset
    
class AssetsPlugin(Plugin):
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir

    def build(self, app):
        app.insert_resource(AssetManager(self.assets_dir))
        # Add default implementations

        manager = app.get_resource(AssetManager)
        manager.add_loader(str, lambda path: load_file(path, str))
        manager.add_loader(bytes, lambda path: load_file(path, bytes))

        app.add_systems(Schedule.Startup, test_asset)

def test_asset(resources: Resources):
    a = resources[AssetManager].load(str, "shaders/main.frag")
    a = resources[AssetManager].load(str, "shaders/main.frag")
    a = resources[AssetManager].load(str, "shaders/main.frag")

    print(a)
