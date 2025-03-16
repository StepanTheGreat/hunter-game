#version 330 core

const int SPRITE_LIMIT = 256;

uniform mat4 projection;
uniform mat3 camera_rot;
uniform vec3 camera_pos;

uniform mat2[SPRITE_LIMIT] sprite_rot;
uniform vec2[SPRITE_LIMIT] sprite_pos;

layout (location = 0) in vec3 position;
layout (location = 1) in vec2 uv;

out vec2 in_uv;

void main()
{   
    vec3 pos = position;
    pos.xz = pos.xz*sprite_rot[gl_InstanceID]+sprite_pos[gl_InstanceID];
    gl_Position = projection*(vec4(camera_rot*(pos-camera_pos), 1));

    in_uv = uv;
}  