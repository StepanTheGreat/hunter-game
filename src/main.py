import pygame as pg
import plugin, modules, config

VIDEO_FLAGS = pg.OPENGL | pg.DOUBLEBUF

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
    "Load the main app config"

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

    builder = plugin.AppBuilder(modules.CoreModulesPlugin(conf))

    return plugin.App(builder)

def main():
    conf = load_config()
    
    pg.display.set_caption(conf.title)
    screen = pg.display.set_mode((conf.width, conf.height), vsync=conf.vsync, flags = VIDEO_FLAGS)
    quitted = False

    application = make_app(conf)
    application.startup()

    while not quitted:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                quitted = True
            else:
                # I decided to not push pg.QUIT, as it will get run with both `render` and `update`,
                # which doesn't really make any sense. Using Schedule.Finalize instead makes more sense, as it
                # will trully be the last schedule to get executed.
                application.push_event(event)

        application.update()
        application.render()

        pg.display.flip()

    application.finalize()
    pg.quit()

if __name__ == "__main__":
    main()