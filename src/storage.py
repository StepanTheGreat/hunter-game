from typing import TypeVar
from typing import Optional

# This is a generic argument that stands for Resource.
# It's highly useful because it allows the intellisense to understand arguments and return types, which
# isn't possible with type erasure. For example:
#
# func(arg: T) -> T
#
# Will tell the intellisense that any type that I use in my argument, will also be returned by the function. 
R = TypeVar("R")

class Storage:
    """
    Inspired by ECS Resources, a storage can store arbitrary values by their types. 
    It's a unique storage, thus only one item of a specific type can be stored at the same time.
    """
    def __init__(self, *resources: any):
        self.database = {}

        for res in resources:
            self.database[type(res)] = res

    def __assert_only_types(self, ty: any):
        assert type(ty) is type, "Storage.get can only accept types, not objects"

    def insert(self, item: R):
        "Insert a new resource, or overwrite an existing one of this type"
        self.database[type(item)] = item
    
    def get(self, ty: R) -> Optional[R]:
        "Get an item by its type. If not present - will return None"
        self.__assert_only_types(ty)

        return self.database.get(ty)

    def __getitem__(self, ty: R) -> R:
        self.__assert_only_types(ty)
        
        return self.database[ty]

    def remove(self, ty: R) -> Optional[R]:
        "Remove and possibly return a value of the provided type from the storage"
        self.__assert_only_types(ty)
        ret = self.get(ty)

        if not ret is None:
            del self.database[ty]

        return ret