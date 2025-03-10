Pygame is nice, but pyglet is way better.
1. It's a pure-python package, which means that it can be directly zip-packed, without any python
installations.
2. It provides efficient hardware rendering for a lot of use-cases, which is incredible to not reinvent
the wheel.
3. It provides direct OpenGL 3 interface, which means that custom shaders and graphics can be easily used with it.

Currently this project already heavily relies on pygame's limited sdl2 port, so things like text are missing,
while features like drawing quads is unstable between pygame versions.

It would be nice to port the existing project to pyglet instead. Ideally, it means the entire app can be packaged
DIRECTLY, using a pure zip archive and a main file which will execute the program. No dependencies - nothing! 