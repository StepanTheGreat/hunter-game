from plugin import Plugin

from .session import SessionContextPlugin
from .events import SessionEventsPlugin
from .systems import SessionSystemsPlugin


class SessionPlugin(Plugin):
    def build(self, app):
        app.add_plugins(
            SessionContextPlugin(),
            SessionEventsPlugin(),
            SessionSystemsPlugin()
        )

