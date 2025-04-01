## Current things to do:
1. ~~Add input manager (collect input, map it to actions and so on). Instead of treating input in terms of~~
   ~~keys - treat it in terms of actions (But essentially it boils down to transforming keys into said actions)~~
2. ~~Add priority for systems (custom execution order. A system can request to be executed earlier or later than~~
   ~~other systems. Essentially it means just sorting them when building the app, so it's not that expensive.~~
   ~~Make sure to collect systems of the same priority into the same lists, since sorting all systems in a giant list~~
   ~~will change their intended priority-local order)~~
3. Add a really simple GUI framework. It should be able to listen for mouse movements, clicks and do actions
   based on that. GUI elements should have an ability to be sorted in a specific order.
   It should be simple for the game to find and modify a specific GUI element at any time.
4. Design the multiplayer architecture. Essentially, it should be shared logic, with additional conditional
   logic that runs on the server (if the client is the server - it would run more stuff).
   Updates are done through events. The server logic updates entities - it should then send these events to
   clients (and thus itself, as a client).

   The player can have a special attribute `main`, that would mean that this player is controlled by the 
   current client. Main players have direct control over their characters, and update events don't get 
   applied to them (well, only movements don't)
5. Add lighting (through normals). It should be similar to how sprites are stored (using uniforms,
   but this time for light). Light should be applied to both tiles and sprites, with additional custom information
   like light's color, position and radius.
6. Add a `SoundManager`, whose entire purpose is... to... you know, play sounds and music... Also
   custom asset loaders for sounds and music!!
7. How about a simple intro? I mean, really simple...? No...? Well, it will be short, like, a few seconds
   max! Thanks!