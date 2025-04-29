#version 330 core

const int LIGHT_LIMIT = 32;
const int SPRITE_LIMIT = 64;

uniform mat4 projection;
uniform mat3 camera_rot;
uniform vec3 camera_pos;
uniform vec2 texture_size;

uniform vec3 sprite_positions[SPRITE_LIMIT];
uniform vec2 sprite_sizes[SPRITE_LIMIT];
uniform mat2 sprite_uv_rects[SPRITE_LIMIT];

uniform vec3[LIGHT_LIMIT] light_positions;
uniform vec3[LIGHT_LIMIT] light_colors;
uniform float[LIGHT_LIMIT] light_radiuses;
uniform int lights_amount;
uniform vec3 ambient_color;

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

// This function is slightly different from the one in base shader, but it applies the same shading for sprites as well.
// For sprites, the only significant difference is that their normal is always pointing towards the player, thus it's calculated based on
// the position of the sprite's vertex and the camera's position
vec3 apply_lights(vec3 material_color, vec3 vert_pos, vec3 normal) {
    vec3 ret_color = material_color * ambient_color;

    for (int i = 0; i < lights_amount; ++i) {
        vec3 light_position = light_positions[i];
        vec3 light_color = light_colors[i];
        float light_radius = light_radiuses[i];

        float light_dist = distance(light_position, vert_pos);
        vec3 light_dir = normalize(vert_pos-light_position);
        float dt = max(dot(normal, light_dir), 0);

        ret_color += light_color*dt*(1-(min(light_dist/light_radius, 1)));
    }

    return ret_color;
}

void main()
{   
    vec3 sprite_pos = sprite_positions[gl_InstanceID];
    vec2 sprite_size = sprite_sizes[gl_InstanceID];
    mat2 uv_rect_mat = sprite_uv_rects[gl_InstanceID];

    vec2 uv_xy = vec2(uv_rect_mat[0].x, uv_rect_mat[0].y);
    vec2 uv_wh = vec2(uv_rect_mat[1].x, uv_rect_mat[1].y);

    // Swapping the Y component with X in arctangent produces a slightly different angle, which in turn
    // produces the "billboard" effect, always looking at the player
    float player_sprite_angle = atan(
        camera_pos.x-sprite_pos.x,
        -camera_pos.z+sprite_pos.z
    );

    mat2 sprite_rot = mat2(
        cos(player_sprite_angle), -sin(player_sprite_angle),
        sin(player_sprite_angle),  cos(player_sprite_angle)
    );

    vec3 pos = position;
    pos.y *= sprite_size.y; 
    pos.xz *= sprite_size.x;
    pos.xz *= sprite_rot;
    pos += sprite_pos;

    vec3 world_pos = pos-camera_pos;
    gl_Position = projection*(vec4(camera_rot*world_pos, 1));

    in_uv = vec2(
        uv_xy.x * uv_mat[0].x + uv_wh.x * uv_mat[1].x,
        uv_xy.y * uv_mat[0].y + uv_wh.y * uv_mat[1].y
    );
    in_uv = vec2(in_uv.x/texture_size.x, in_uv.y/texture_size.y);

    in_color = apply_lights(vec3(1, 1, 1), pos, normalize(world_pos));
}  