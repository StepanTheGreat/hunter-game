from plugin import event

@event
class PushGUICommand:
    "A command that pushed GUI element onto the GUI stack"
    def __init__(self, new_elements: list):
        self.new_elements: list = new_elements

@event
class PopGUICommand:
    "A command to pop the current GUI elements layer from the GUI stack. If nothing is present - does nothing"

@event
class ReplaceGUICommand:
    "Essentially a combination of `PopGUICommand` + `PushGUICommand` = remove the current GUI layer and push a new one"
    def __init__(self, new_elements: list):
        self.new_elements = new_elements

@event
class ClearGUICommand:
    "A command for clearing out all GUI layers from the stack"