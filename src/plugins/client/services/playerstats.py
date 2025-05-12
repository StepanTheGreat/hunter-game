from plugin import Plugin, Resources

from plugins.client.commands import UpdatePlayerStatsHealthCommand, ResetPlayerStatsHealthCommand

class PlayerStats:
    "Stores global player related information. Useful for GUI and visualisations, since its a shared resource"
    def __init__(self):
        self.health: float = 0
        "Stores the player's health in percentages"

    def update_health(self, new_health: float):
        assert 0 <= new_health <= 1
        
        self.health = new_health

    def get_health(self) -> float:
        return self.health

def on_reset_player_health_command(resources: Resources, _):
    resources[PlayerStats].update_health(1)

def on_update_player_health_command(resources: Resources, command: UpdatePlayerStatsHealthCommand):
    resources[PlayerStats].update_health(command.value)
    
class PlayerStatsPlugin(Plugin):
    def build(self, app):
        app.insert_resource(PlayerStats())

        app.add_event_listener(ResetPlayerStatsHealthCommand, on_reset_player_health_command)
        app.add_event_listener(UpdatePlayerStatsHealthCommand, on_update_player_health_command)