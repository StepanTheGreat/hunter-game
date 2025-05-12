from plugin import Plugin, Resources

from core.sound import SoundManager

from plugins.client.commands import GameNotificationCommand, CheckoutSceneCommand, CheckoutScene

from plugins.shared.interfaces.stage import GameNotification

def on_checkout_scene(resources: Resources, command: CheckoutSceneCommand):
    "When we transition a scene, we would like to play some music on loop"

    sounds = resources[SoundManager]

    scene = command.new_scene

    new_music = "music/aerial.ogg" if scene is CheckoutScene.MainMenu else "music/crystal_cola.ogg"

    sounds.stop_music()
    sounds.load_music(new_music)
    sounds.play_music(loops=-1)

def on_game_notification(resources: Resources, command: GameNotificationCommand):
    "When the game starts - we would like to silence everything. BUT, when the lights are on - we will play some cool soundtrack!"

    sounds = resources[SoundManager]

    notification = command.notification

    if notification == GameNotification.GameStarted:
        sounds.stop_music()
    elif notification == GameNotification.LightsOn:
        sounds.load_music("music/hackers.ogg")
        sounds.play_music(loops=-1, fade_ms=1000)

class MusicHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(CheckoutSceneCommand, on_checkout_scene)

        app.add_event_listener(GameNotificationCommand, on_game_notification)
