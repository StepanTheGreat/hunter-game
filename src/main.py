import pygame as pg
import plugin, core

from plugins import PluginsCollection
from app_config import AppConfig, load_config

def make_app(conf: AppConfig) -> plugin.App:
    "Construct the main application"

    builder = plugin.AppBuilder(
        core.CoreModulesPlugin(conf),
        PluginsCollection()
    )

    return plugin.App(builder)

def main():
    app = make_app(load_config())
    app.run()

if __name__ == "__main__":
    main()