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
    def __init__(self):
        self.auto_resources = []
        """
        Auto resources are resources that will get automatically inserted when enterting the scene,
        and removed when quitting.
        """

    def add_auto_resources(self, *resources: object):
        "Add an unspecified amount of automatic resources to the list"
        self.auto_resources.extend(resources)

    def _init(self, resources: Resources):
        self.pre_init(resources)
        for resource in self.auto_resources:
            resources.insert(resource)
        self.post_init(resources)

    def pre_init(self, resources: Resources):
        "The bundle's pre-initialisation logic (before inserting automatic resources)"

    def post_init(self, resources: Resources):
        "The bundle's post-initialisation logic (after inserting automatic resources)"

    def _destroy(self, resources: Resources):
        self.pre_destroy(resources)
        for resource in self.auto_resources:
            resources.remove(type(resource))
        self.post_destroy(resources)

    def pre_destroy(self, resources: Resources):
        "The logic that's run before cleaning up automatic resources"

    def post_destroy(self, resources: Resources):
        "The logic that's run after cleaning up automatic resources"

class SceneManager:
    "Simply a global resource for checking app's state"
    def __init__(self, resources: Resources, default_scene: SceneBundle):
        self.resources = resources
        self.current_scene = None

        self.insert_scene(default_scene)

    def insert_scene(self, new_scene: SceneBundle):
        "Insert a new scene bundle into this scene manager. The previous scene will get deinitialized and overwritten"
        if self.current_scene is not None:
            self.current_scene._destroy(self.resources)
        
        self.current_scene = new_scene
        self.current_scene._init(self.resources)

    def reload_scene(self):
        "Reload the current scene. Highly useful when changing settings like language for example"
        if self.current_scene is not None:
            self.insert_scene(self.current_scene)