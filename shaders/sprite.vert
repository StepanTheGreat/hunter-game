#version 330 core

uniform mat4 projection;
uniform mat3 camera_rot;
uniform vec3 camera_pos;

uniform mat2 sprite_rot;
uniform vec2 sprite_pos;

layout (location = 0) in vec3 position;
layout (location = 1) in vec2 uv;

out vec2 in_uv;

void main()
{   
    mat2 s = sprite_rot;
    mat3 r = camera_rot;
    mat4 p = projection;
    vec2 a = sprite_pos;

    vec3 pos = position;
    pos.xz = pos.xz*sprite_rot+sprite_pos;
    gl_Position = projection*(vec4(camera_rot*(pos-camera_pos), 1));

    in_uv = uv;
}  