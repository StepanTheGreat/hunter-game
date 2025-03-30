import pygame as pg

from enum import Enum
from typing import Union
from json import loads
from file import load_file_str
from app_config import CONFIG

from plugin import AppBuilder, Plugin, Resources, Schedule

from core.assets import AssetManager, add_loaders

class KeyMappings:
    "Essentially this is just a collection of tuple key mappings, but, as an asset! It is loaded from json"
    def __init__(self, mappings: tuple[tuple[str, str], ...]):
        self.mappings = mappings

def loader_key_mappings(_: Resources, path: str) -> KeyMappings:
    "A key mappings loader. It will crash if the mappings file has incorrect key/value types"

    json_s = load_file_str(path)
    parsed_mappings: dict = loads(json_s)

    mappings = []
    for action_key, action_name in parsed_mappings.items():
        assert type(action_name) == str, "JSON key mappings have incorrect types"
        assert type(action_key) == str, "JSON key mappings have incorrect types"

        mappings.append((action_key, action_name))
    
    return KeyMappings(tuple(mappings))


class MouseButton(Enum):
    "A simple enumerator for mouse buttons"
    Left = 0
    Center = 1
    Right = 2

class InputManager:
    def __init__(self):
        self.keys_down: set = None
        self.mouse_position = None
        self.mouse_buttons = None

        self.key_action_map: dict[str, int] = {}
        "This dictionary directly maps action names to pygame keys"

        self.update()

    def update(self):
        "Update the internal input state. Called automatically "
        self.keys_down = pg.key.get_pressed()
        self.mouse_position = pg.mouse.get_pos()
        self.mouse_buttons = pg.mouse.get_pressed(3)

    def apply_key_mappings(self, mappings: KeyMappings):
        "Apply a custom key map to this input manager"
        for action_key_name, action_name in mappings.mappings:
            # Since pygame internally uses integer keys and our mappings use string key names - we need to
            # convert those
            self.key_action_map[action_name] = pg.key.key_code(action_key_name)

    def is_action_down(self, action_name: str) -> bool:
        "Check if the provided action is down (i.e. its underlying keys)"
        return self.keys_down[
            self.key_action_map[action_name]
        ]
    
    def is_mouse_down(self, button: MouseButton) -> bool:
        return self.mouse_buttons[button]
    
    def __getitem__(self, action: Union[str, MouseButton]) -> bool:
        # Just a shortcut, but we can check both the mouse buttons and key actions!
        return self.is_action_down(action) if type(action) == str else self.is_mouse_down(action)            
    
    def get_mouse_pos(self) -> tuple[int, int]:
        return self.mouse_position

def update_input(resources: Resources):
    "Simply update the input with new key and mouse information every frame"
    resources[InputManager].update()

def load_default_keys(resources: Resources):
    "At the start of the application we're going to load the keys from the config path"
    resources[InputManager].apply_key_mappings(
        resources[AssetManager].load(KeyMappings, CONFIG.keys)
    )

class InputPlugin(Plugin):
    def build(self, app):
        app.insert_resource(InputManager())
        app.add_systems(Schedule.Startup, load_default_keys)
        app.add_systems(Schedule.First, update_input)

        # Add our custom key mappings loader!
        add_loaders(app, (KeyMappings, loader_key_mappings))
