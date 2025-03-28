import plugin, core

from plugins import PluginsCollection

def make_app() -> plugin.App:
    "Construct the main application"

    return plugin.App(plugin.AppBuilder(
        core.CoreModulesPlugin(),
        PluginsCollection()
    ))

def main():
    app = make_app()
    app.run()

if __name__ == "__main__":
    main()