import plugin

from core import ClientCoreModulesPlugin
from plugins.client import ClientPluginCollection

from multiprocessing import freeze_support

def make_app() -> plugin.App:
    "Construct the main application"

    return plugin.App(plugin.AppBuilder(
        ClientCoreModulesPlugin(),
        ClientPluginCollection()
    ))

def main():
    app = make_app()
    app.run()

if __name__ == "__main__":
    freeze_support() 
    # This is required when using pyinstaller for producing python binaries

    main()