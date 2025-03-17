# Maze Runner
## A school project almost fully in python (if possible, wasm packages can be used for optimisations)

It uses graphs algorithms for path searching (A*)

Basically, this is a 2.5D game where you spawn in a maze, and escape monster that track and move towards you in the maze.

This game uses raycasting to view the world in first perspective and A* algorithm for finding the best path
to the player. 

The maps are premade using Tiled, using premade public assets for public use

## Coordinates
The coordinates in the game are divided into 2 types:
- Game logic coordinates
- Render coordinates.

The only difference between the 2 is that in game coordinates, Y's up goes negative, while in
render coordinates it goes positive.

A lot of logic relies on topleft to bottomright coordinates, like rectangles or basic logic.

If you see negative Y coordinates in the codebase in rendering-related code - that's the reason. 
If you see them outside though - that's a bug on my part.  