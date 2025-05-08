from plugin import event

@event
class ResetEntityUIDManagerCommand:
    "A command for resetting the entity UID manager. It should be reset EVERY SESSION"