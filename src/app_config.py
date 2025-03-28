from modules.config import typed_dataclass, load_config_file

@typed_dataclass
class AppConfig:
    """
    The main application configuration that can be loaded from json. 
    All its fields can be overwritten with new values
    """
    width: int = 768
    height: int = 560
    vsync: bool = True
    fps: int = 60
    title: str = "Maze Runner"
    assets_dir: str = "../assets"

def load_config() -> AppConfig:
    # I added a config.json file from an urgent need of constantly changing different app settings
    # like width, height or fps. One problem however... git keeps track of every single change. 
    # Ignoring the file would mean that someone would need to manually recreate said file, which isn't ideal at all.
    # My solution here is an optional configuration file that can overwrite some settings
    try:
        conf = load_config_file(AppConfig, "../config.json")
    except FileNotFoundError:
        conf = AppConfig()
    return conf

CONFIG: AppConfig = load_config()