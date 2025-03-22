import pygame as pg
import plugin, core, config

from plugins import PluginsCollection

@config.typed_dataclass
class AppConfig:
    """
    The main application configuration that can get loaded from json. 
    All its fields can be overwritten with new values
    """
    width: int = 768
    height: int = 560
    vsync: bool = True
    fps: int = 60
    title: str = "Maze Runner"

def load_config() -> AppConfig:
    # I added a config.json file of an urgent need of constantly chaning different app settings
    # like width, height or fps. One problem however... git keeps track of every single change. 
    # Ignoring the file would mean that someone would need to manually recreate said file, which isn't ideal at all.
    # My solution here is an optional configuration file that can overwrite some settings
    try:
        conf = config.load_config_file(AppConfig, "../config.json")
    except FileNotFoundError:
        conf = AppConfig()
    return conf

def make_app(conf: AppConfig) -> plugin.App:
    "Construct the main application"

    builder = plugin.AppBuilder(core.CoreModulesPlugin(conf))
    builder.add_plugins(PluginsCollection)

    return plugin.App(builder)

def main():
    app = make_app(load_config())
    app.startup()

    app.run()

    while not app.should_quit():
        app.update()
        app.render()

    app.finalize()

if __name__ == "__main__":
    main()