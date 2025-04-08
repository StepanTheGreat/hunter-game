#version 330 core

const float LIGHT_RADIUS = 150;
const int LIGHT_LIMIT = 256;

uniform mat4 projection;
uniform mat3 camera_rot;
uniform vec3 camera_pos;

uniform vec3[LIGHT_LIMIT] light_positions;
uniform vec3[LIGHT_LIMIT] light_colors;
uniform int lights_amount;

layout (location = 0) in vec3 position;
layout (location = 1) in vec3 normal;
layout (location = 2) in vec3 color;
layout (location = 3) in vec2 uv;

out vec3 in_color;
out vec2 in_uv;

void main() {
    vec3 pos = camera_rot*(position-camera_pos);
    gl_Position = projection*(vec4(pos, 1));

    in_color = color;

    for (int i = 0; i < lights_amount; ++i) {
        vec3 light_position = light_positions[i];
        vec3 light_color = light_colors[i];

        float light_dist = distance(light_position + normal/1000, position);
        vec3 light_dir = normalize(position-light_position);
        float dt = max(-dot(normal, light_dir), 0);

        in_color += light_color*(1-(min(light_dist/LIGHT_RADIUS, 1)));
        // in_color += light_color*(1-clamp(light_dist/LIGHT_RADIUS, 0, 1));
    }

    in_uv = uv;
}  