from plugin import Plugin

from .player import ClientPlayerPlugin
<<<<<<< HEAD
from .policeman import ClientPolicemanPlugin
=======
from .characters import ClientCharactersPlugin
from .diamond import ClientDiamondPlugin
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75

class ClientEntitiesPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            ClientPlayerPlugin(),
<<<<<<< HEAD
            ClientPolicemanPlugin()
=======
            ClientCharactersPlugin(),
            ClientDiamondPlugin()
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
        )