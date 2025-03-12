# Performance problem

Currently, casting rays is extremely efficient, since the main ray-casting module was remade in rust.
Now, after profiling, it seems like the MAIN bottleneck that causes the FPS to drop is the `render_rays`
function, which simply iterates over ray casted results and then draws them line by line.

This sole function takes 0.016 milliseconds PER CALL, which is enough to drop the FPS by half.
My main theory behind why this could be so slow is the fact that there's too much geometry to be sent
when drawing every single line. A quad in sdl2 I suppose consists of:
- Position (2 floats) = 8
- UV (2 floats) = 8
- Color (3 floats) = 12

Which in total sums up to 28 bytes PER vertex.
A single quad consists of 4 (ignoring the other 2 that will be indexed in the index buffer), and in total we will
have... 112 bytes per quad! You could also add another 12 bytes from the index buffer, but this doesn't change much.

For an entire screen resolution, let's say 1280, that's 143K bytes for the entire screen, sent out every frame for
no actual reason.

Did I mention glass? The fact that it almost doubles if not triples this number? So we could have way more
than we think.


## Some additional context:
1. Loading a world with solely 1 type of block doesn't increase the performance by much, suggesting that the problem
is not tied to failed texture batching.
2. It's unclear whether color tiles or texture tiles are different, but loading a world with solely colored textures
seems to produce similar results. Almost 30/40% of the execution, although it's way faster since it lacks transparent
tiles.
3. It seems like another half of the execution is spent in `render_rays` simply calculating everything and issuing
draw calls. Optimizing this could save at least a half of the entire execution time.

## Possible solutions
Since the bottleneck lies in both draw call issuing and sending draw operations to the GPU, my best bet would be
to kill both by doing all of these operations on the GPU (like it was always supposed to do honestly) via 
instancing. Still, a lot of information has to be prepared and looped over, but if it is possible - it could save
some time.

Another solution to shave a third of this execution could be to automatically calculate everything on the rust side.
If raycasting is used purely for rendering - it could actually serve as a valid solution (the GPU one can be made
later ), but currently, it's difficult to say for sure.