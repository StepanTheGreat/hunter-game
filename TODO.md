# Done!

## Modularize the thing, so that it's actually usable and extensible. 
You could use a plugin-like system like in ECS frameworks. Systems *could also* be a great way of abstracting
functionality.

## Plan
1. Fix sprite rotations, so no matter their position they always look into your direction.
2. Create a basic game plan
3. Modularize every game component into a separate module. A plugin system could be used, where a plugin
has systems that are executed at different schedules. Resources can also help here organize application data.
4. Model a simple UDP network protocol, that would feature reliability, data integrity checks and dublicate avoidance.
5. Add a simple encryption to the traffic using public/private keys. In the future, a simple database of reliable
signatures could be use to avoid Man In The Middle attacks
6. Make a basic multiplayer support using the lockstep system
7. Add lighting to the game

... More to see 