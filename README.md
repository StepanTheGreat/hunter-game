# Hunter game

A simple 3D game made in python using `moderngl`, `pygame`, `pyopenal` and so on.
Currently the planned idea is to make a simple hunting game, where players divide into 2 category:
The boss, and the hunters. The boss is always alone, it has a lot of health, and they have a specific
task to do to win (either collect all items or anything else). The idea behind hunters is that they 
have to stop the boss BEFORE they achieve all their tasks.

Hunters have a small amount of health, but can use ranged weapons.
The boss has a lot of health, but only can deal melee damage. Still, they're pretty deadly when put in a
1v1 against a hunter, that's why there are multiple hunters.

The game should feature multiplayer, so that people can open rooms, join, play - then start over
or go do something else.

## Some basic architecture

The game is designed around plugins and systems. A system is a function that runs in a specific stage of
the application (be it on startup, every frame, every fixed frame and so on). We're using systems
to decouple logic, as it makes it extremely convenient to add new stuff. This does however introduce
global state, which has its own management issues.
Plugins are just simple "bundles", that contain registering logic for the app. A system/resource/event listener can be attached to the application, but instead of importing everything in a single file - a plugin system allows one plugin to load another one. Recursively.

For entities in the game this project uses ECS, which... actually doesn't really have any benefit,
besides decoupled client/server logic? It's a bit difficult to say. But it works quite nice with the
systems setup we already have

For networking this project uses an RPC approach, where both the client and the server interact with each other through "network functions". They're essentially functions that have unique integer identifiers (up to a byte), but instead of accepting python values - they use byte values instead.

# Licensing
The project isn't licensed entirely under the same license. All code (be it in `src` or `assets/shaders` directories) is licensed under Apache-2.0 license (in the `LICENSE_CODE`) All the other assets like music,
textures, fonts and so on either come with their own licenses in their respective directories, or are 
hand-drawn. This notice will change throughout project's development, especially regarding some types of
assets.