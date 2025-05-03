import plugin, core

from plugins.client import ClientPluginCollection

def make_app() -> plugin.App:
    "Construct the main application"

    return plugin.App(plugin.AppBuilder(
        core.ClientCoreModulesPlugin(),
        ClientPluginCollection()
    ))

def main():
    app = make_app()
    app.run()

if __name__ == "__main__":
    main()