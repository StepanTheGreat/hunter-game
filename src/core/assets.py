from typing import TypeVar, Callable, Optional, Type
from plugin import Resources, Plugin, AppBuilder

# Asset
A = TypeVar("A")

class AssetManager:
    """
    An asset manager is an asster storage, loader and cache at the same time.

    An assets directory should be given **without** trailing slashes
    """
    def __init__(self, resources: Resources, assets_dir: str):

        # To avoid constantly passing resources when loading assets, the asset manager will keep
        # them in its attributes instead
        self.resources: Resources = resources

        self.assets_dir = assets_dir + "/"
        self.database: dict[type, dict[str, object]] = {}
        "A database groups assets by their type. Each group is also a small database, but this time of their names"

        self.loaders: dict[type, Callable[[Resources, str], A]] = {}
        """
        A database of loaders. An asset type has to first have a registered load function. 
        In any other case, an asset manager doesn't know how to load assets
        """

    def asset_path(self, path: str) -> str:
        "Transform this path into an absolute assets path"
        return self.assets_dir+path

    def add_loader(self, ty: Type[A], f: Callable[[Resources, str], A]):
        "Add an asset loader function for the provided asset type"
        self.loaders[ty] = f

    def store(self, path: str, asset: A):
        "Store an object under provided path. Basically manual caching"
        ty = type(asset)
        if ty in self.database:
            self.database[ty][path] = asset
        else:
            self.database[ty] = {path: asset}

    def get(self, ty: Type[A], path: str) -> Optional[A]:
        "Try get an asset without firing any loading logic"
        # First check if the type exists
        if (ty_group := self.database.get(ty)) is not None:
            # Then check if said group has an asset
            if (asset := ty_group.get(path)) is not None:
                return asset
            
        return None
    
    def load_abs(self, ty: Type[A], path: str, **kwargs) -> A: 
        assert ty in self.loaders, "The requested asset type doesn't have a loader"
        
        # If we're able to get this asset from our database, we will return it early.
        if (cached_asset := self.get(ty, path)) is not None:
            return cached_asset
        else:
            # Load the asset using the registered loader function
            loaded_asset = self.loaders[ty](self.resources, path, **kwargs)

            # Initialize a new type map if it doesn't exist
            if ty not in self.database:
                self.database[ty] = {}

            # Store this asset for future use
            self.database[ty][path] = loaded_asset

            return loaded_asset

    def load(self, ty: Type[A], path: str, **kwargs) -> A:
        return self.load_abs(ty, self.asset_path(path), **kwargs)
    
class AssetsPlugin(Plugin):
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir

    def build(self, app):
        app.insert_resource(AssetManager(app.get_resources(), self.assets_dir)  )


def add_loaders(builder: AppBuilder, *loaders: tuple[Type[A], Callable[[Resources, str], A]]):
    """
    A convenient function for mass registering loaders. 
    Takes the app builder and an unlimited amount of tuple loader arguments: `(type, loader_func), ...` 
    """
    assets = builder.get_resource(AssetManager)
    for loader_ty, loader_func in loaders:
        assets.add_loader(loader_ty, loader_func)