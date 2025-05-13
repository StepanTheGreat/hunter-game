# Hunter game
![gameplay](./gameplay.gif)

A simple, 3D real-time multiplayer action game for up to 5 players per session. The essential idea is that in the game there are 2 teams: the police team (up to 4 players) and the
robber team (a single character chosen randomly). The goal of the robber is to collect all the diamonds on the map, while the policemen should defeat him before this happens. 
The robber has some buffs like increased speed and more health, thus making it a deadly encounter for solo cops on close range.
The game starts in the dark - the robber has a chance to either grab his first diamond, or kill a policeman. After, the lights turn on and the main action starts, with all
cops running towards the robber and trying to kill him.

## How to play
This game is server based, meaning that to play, you must have a server on the current network. You can create one with "Create Game", which will start a new server on the currently
available network (localhost works as well). All servers periodically (once in 5 seconds) send broadcast packets on the network; if a game client in the main menu sees one - they
will get immediately connected to the broadcasted server. This is a quite stupid implementation for thousands of reasons, but was left there due to time restrictions.

Depeding on your keyboard layout (the default is azerty, though you can change it by creating a separate config.json files and replacing the `keys` attribute to something different):
- **Move**: AWSD / QZSD
- **Turn around**: left/right arrow keys
- **Shoot**: space (just holding it is enough)

While in a server, all players must be ready to start the game. Pressing on the center button will switch the current status (it shows the current status, not the next one like
some games do). You can always quit the game whenever you want. A game server that already started the game will no longer accept connections nor broadcast its presence, thus
a client won't be able to connect back.

## Some basic architecture

The game is designed around plugins and systems. A system is a function that runs in a specific stage of
the application (be it on startup, every frame, every fixed frame and so on). We're using systems
to decouple logic, as it makes it extremely convenient to add new stuff. This does however introduce
global state, which has its own management issues.
Plugins are just simple "bundles", that contain registering logic for the app. A system/resource/event listener can be attached to the application, but instead of importing everything in a single file - a plugin system allows one plugin to load another one. Recursively.

For entities in the game this project uses ECS, which... actually doesn't really have any benefit, besides decoupled client/server logic? 
It's a bit difficult to say. But it works quite nice with the systems setup we already have. As an inspiration I chosen `esper`, but this project makes it a bit more performant
by utilizing archetypes, thus reducing the emount of work it takes to query an entity.

For networking this project uses an RPC approach, where both the client and the server interact with each other through "network functions". They're essentially functions that have unique integer identifiers (up to a byte), but instead of accepting python values - they use byte values instead. You can look into the `rpcs` directory under `plugins` to see
an example of these.

## This project is no longer maintained
It's done. It's over. Finally done.
This was my experimentation, and halfway through the game I realized that using Python for these kind of projects is simply unsuitable. No matter how hard you try to document
something, how hard you try to type something - it simply doesn't matter. Sure, Python is extremely convenient and fast to use, but sometimes we want our code to be more strict
regarding types, structures and so on. Half of the entire code in this repo wouldn't even exist, was it made in a simple compiled language (like numpy list for example).

Overall, while I think this project brought me some extremely valuable experience and I got a go at building something I never tried before - I did realize that some decisions
that were made were... not the best...

# Licensing
The project isn't licensed entirely under the same license. All code (be it in `src` or `assets/shaders` directories) is licensed under Apache-2.0 license (in the `LICENSE_CODE`).
All the other assets like music, textures, fonts and so on either come with their own licenses in their respective directories, or are hand-drawn. 
