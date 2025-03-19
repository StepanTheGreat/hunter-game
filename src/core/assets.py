from typing import TypeVar, Callable

# Asset
A = TypeVar("A", type)

class AssetLoader:
    def extensions() -> tuple[str, ...]:
        pass

class AssetManager:
    "An asset manager is an asster storage, loader and cache at the same time"
    def __init__(self):
        self.database: dict[type, dict[str, object]] = {}
        "A database groups assets by their type. Each group is also a small database, but this time of their names"

        self.loaders: dict[type, Callable[[A, str], A]] = {}
        """
        A database of loaders. An asset type has to first have a registered load function. 
        In any other case, an asset manager doesn't know how to load assets
        """

    def load(self, ty: A, path: str) -> A:
        assert ty in self.loaders, "The requested asset type doesn't have a loader"

        asset = self.loaders[ty](ty, path)