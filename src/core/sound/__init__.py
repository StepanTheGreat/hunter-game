import pygame as pg

from plugin import Plugin, Schedule, Resources

from core.assets import AssetManager, add_loaders

from random import choice as rand_choice
from file import load_json_and_validate, get_file_dir

LISTENER_RADIUS = 100

class Sound:
    "A sound container for pygame sounds"
    def __init__(self, sound: pg.mixer.Sound):
        self.sound: pg.mixer.Sound = sound

class SoundPack:
    """
    A sound pack is a pack of different sounds. The idea is to store similar sounds by their purpose
    and play them randomly.
    """
    def __init__(self, sounds: tuple[Sound]):
        assert len(sounds) > 0, "Can't create an empty sound pack!"

        self.sounds = sounds

    def get_random(self) -> Sound:
        "Get a random sound from this pack"

        return rand_choice(self.sounds)

SOUND_PACK_JSON_SCHEMA = {
    "type": "array",
    "items": {"type": "string"}
}

def loader_sound(_: Resources, path: str) -> Sound:
    "A pygame sound loader"

    return Sound(pg.mixer.Sound(path))

def loader_soundpack(_: Resources, path: str) -> SoundPack:
    "A loader for soundpacks"

    soundpack = load_json_and_validate(path, SOUND_PACK_JSON_SCHEMA)

    soundpack_dir = get_file_dir(path)

    

class SoundManager:
    def __init__(self, assets: AssetManager):
        pg.mixer.init()

        self.assets = assets

        self.listener_pos: pg.Vector2 = pg.Vector2(0, 0)
        self.listener_radius: float = LISTENER_RADIUS

    def play_sound(self, sound: Sound):
        """
        Play the provided sound at the provided position. (Highly simple calculations)
        If there are too many sounds - will not add this sound to the source list until
        it's freed.
        """
        sound.sound.play()

    def play_sound(self, sound: Sound):
        "Play a sound without any spatial trasnformations"
        sound.sound.play()

    def play_soundpack(self, soundpack: SoundPack):
        "Essentially the same as `play_sound`, but for sound packs."

    def queue_music(self, music_path: str, loops: int = 0):
        pg.mixer_music.queue(self.assets.asset_path(music_path), loops=loops)

    def load_music(self, music_path: str):
        pg.mixer_music.load(self.assets.asset_path(music_path))

    def play_music(self, loops: int = 0, start: float = 0, fade_ms: int = 0):
        pg.mixer_music.play(loops, start, fade_ms)

    def stop_music(self):
        pg.mixer_music.stop()
        pg.mixer_music.unload()
    
    def set_listener_position(
        self, 
        position: tuple[float, float], 
    ):
        self.listener_pos.x = position[0]
        self.listener_pos.y = position[1]

class SoundPlugin(Plugin):
    def build(self, app):
        app.insert_resource(SoundManager(app.get_resource(AssetManager)))

        add_loaders(app,
            (Sound, loader_sound)            
        )