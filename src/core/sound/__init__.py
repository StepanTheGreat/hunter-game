import pygame as pg

from core.assets import AssetManager, add_loaders

from plugin import Plugin, Schedule, Resources

LISTENER_RADIUS = 100

class Sound:
    "A sound container for pygame sounds"
    def __init__(self, sound: pg.mixer.Sound):
        self.sound: pg.mixer.Sound = sound

def loader_sound(_: Resources, path: str) -> Sound:
    "A pygame sound loader"

    return Sound(pg.mixer.Sound(path))

class SoundManager:
    def __init__(self, assets: AssetManager):
        pg.mixer.init()

        self.assets = assets

        self.listener_pos: pg.Vector2 = pg.Vector2(0, 0)
        self.listener_radius: float = LISTENER_RADIUS

    def play_sound_at(self, sound: Sound, position: tuple[int, int]):
        """
        Play the provided sound at the provided position. (Highly simple calculations)
        If there are too many sounds - will not add this sound to the source list until
        it's freed.
        """
        sound: pg.mixer.Sound = sound.sound

        dist = self.listener_pos.distance_to(position)
        volume = self.listener_radius/((dist+1)**2) # Basic attenuation based volume 
        volume = min(volume, 1)

        sound.set_volume(volume)
        sound.play()

    def play_sound(self, sound: Sound):
        "Play a sound without any spatial trasnformations"
        sound.sound.play()

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