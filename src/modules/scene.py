from plugin import Resources

class SceneBundle:
    """
    A class that contains a collection of resources related to a scene. This allows composing a scene using
    different resources and systems.

    For example, a map renderer plugin will only render the map when the `MapModel` resource is present. 
    We don't want our map model to persist at all times however. Using scenes, we can add the `MapModel` as a
    scene local resource that will get inserted when entering the scene, and automatically removed when
    quitting.

    But a scene can also have a custom constructor, initialisation and removal logic, so generally - 
    you have to freedom to do whatever you want!
    """
    def __init__(self, *resources: object):
        self.auto_resources = resources
        """
        Auto resources are resources that will get automatically inserted when enterting the scene,
        and removed when quitting.
        """

    def init(self, resources: Resources):
        """
        The bundle's registration logic. By default it will insert all automatic resources
        """
        [resources.insert(resource) for resource in self.auto_resources]

    def destroy(self, resources: Resources):
        """
        The bundle's removal logic (when overwritten by another scene bundle). By default it will
        simply remove all scene's automatic resources.
        """
        [resources.remove(type(resource)) for resource in self.auto_resources]

class SceneManager:
    "Simply a global resource for checking app's state"
    def __init__(self, resources: Resources, default_scene: SceneBundle):
        self.resources = resources
        self.current_scene = None

    def insert_scene(self, new_scene: SceneBundle):
        "Insert a new scene bundle into this scene manager. The previous scene will get deinitialized and overwritten"
        if self.current_scene is not None:
            self.current_scene.destroy(self.resources)
        
        self.current_scene = new_scene
        self.current_scene.init(self.resources)