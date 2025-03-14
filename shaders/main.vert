#version 330 core

uniform mat4 projection;
uniform mat3 camera_rot;
uniform vec3 camera_pos;

layout (location = 0) in vec3 position;
layout (location = 1) in vec3 color;

out vec3 in_color;

void main()
{
    mat3 a = camera_rot;
    vec3 b = camera_pos;
    vec3 pos = camera_rot*(position-camera_pos);
    gl_Position = projection*(vec4(pos, 1));
    in_color = color;
}  