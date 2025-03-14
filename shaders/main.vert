#version 330 core

uniform mat4 projection;
uniform mat4 camera;

layout (location = 0) in vec3 position;
layout (location = 1) in vec3 color;

out vec3 in_color;

void main()
{
    gl_Position = projection*camera*vec4(position, 1);
    in_color = color;
}  