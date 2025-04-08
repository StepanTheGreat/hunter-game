#version 330 core

const float LIGHT_RADIUS = 600;

const int SPRITE_LIMIT = 256;

uniform mat4 projection;
uniform mat3 camera_rot;
uniform vec3 camera_pos;

uniform vec2[SPRITE_LIMIT] sprite_positions;
uniform vec2[SPRITE_LIMIT] sprite_sizes;
uniform mat2[SPRITE_LIMIT] sprite_uv_rects;

layout (location = 0) in vec3 position;
layout (location = 1) in mat2 uv_mat;

// So the hell is a uv-matrix? Basically, it's a way to tell our shader which vertex to use.
//
// For instanced sprites, it would be a great feature to be able to tell which part of the texture we would
// like to use. Using a uv matrix (that is a matrix of 0 and 1), we can tell whether to use the top-left
// corner, or the top-right corner, or any other coordinate.
//
// Sprites then need to send their uv_rects, which are matrices of: [x, y, x+w, y+h]

out vec2 in_uv;
out vec3 in_color;

void main()
{   
    vec2 sprite_pos = sprite_positions[gl_InstanceID];
    vec2 sprite_size = sprite_sizes[gl_InstanceID];
    mat2 uv_rect = sprite_uv_rects[gl_InstanceID];

    // Swapping the Y component with X in arctangent produces a slightly different angle, which in turn
    // produces the "billboard" effect, always looking at the player
    float player_sprite_angle = atan(
        camera_pos.x-sprite_pos.x,
        -camera_pos.z+sprite_pos.y
    );

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

    in_uv = vec2(
        uv_rect[0].x * uv_mat[0].x + uv_rect[1].x * uv_mat[1].x,
        uv_rect[0].y * uv_mat[0].y + uv_rect[1].y * uv_mat[1].y
    );

    in_color = vec3(1, 1, 1) * 1-clamp(0, distance(pos, camera_pos)/LIGHT_RADIUS, 1);
}  