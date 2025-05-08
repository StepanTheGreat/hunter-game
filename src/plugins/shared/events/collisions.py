from plugin import event

@event
class CollisionEvent:
    """
    Fired whenever a collision between a sensor and an another collider has happened. 
    
    Sensor entity is the entity that listens to said collisions.
    Hit entity is the entity that touched our entity. It's important to note than 2 sensors can absolutely
    collide, so this event will also affect sensor/sensor collisions
    """
    def __init__(self, sensor_entity: int, hit_entity: int, hit_collider_ty: type):
        self.sensor_entity = sensor_entity

        self.hit_entity = hit_entity
        self.hit_collider_ty = hit_collider_ty