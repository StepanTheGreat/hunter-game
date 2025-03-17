#version 330 core

const int SPRITE_LIMIT = 256;

uniform mat4 projection;
uniform mat3 camera_rot;
uniform vec3 camera_pos;

uniform vec2[SPRITE_LIMIT] sprite_positions;
uniform vec2[SPRITE_LIMIT] sprite_sizes;

layout (location = 0) in vec3 position;
layout (location = 1) in vec2 uv;

out vec2 in_uv;

void main()
{   
    vec2 sprite_pos = sprite_positions[gl_InstanceID];
    vec2 sprite_size = sprite_sizes[gl_InstanceID];

    // We're adding sprite_pos.y+camera_pos.z, because 
    float player_sprite_angle = atan(sprite_pos.x-camera_pos.x, sprite_pos.y+camera_pos.z);
    mat2 sprite_rot = mat2(
        cos(player_sprite_angle), -sin(player_sprite_angle),
        sin(player_sprite_angle),  cos(player_sprite_angle)
    );

    vec3 pos = position;
    pos.y *= sprite_size.y; 
    pos.xz *= sprite_size.x;
    pos.xz *= sprite_rot;
    pos.xz += sprite_pos;
    gl_Position = projection*(vec4(camera_rot*(pos-camera_pos), 1));

    in_uv = uv;
}  