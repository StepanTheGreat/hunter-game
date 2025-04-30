#version 330 core

const int LIGHT_LIMIT = 32;

uniform mat4 projection;
uniform mat3 camera_rot;
uniform vec3 camera_pos;
uniform vec2 texture_size;

uniform vec3[LIGHT_LIMIT] light_positions;
uniform vec3[LIGHT_LIMIT] light_colors;
uniform float[LIGHT_LIMIT] light_radiuses;
uniform float[LIGHT_LIMIT] light_luminosities;

uniform int lights_amount;
uniform vec3 ambient_color;

layout (location = 0) in vec3 position;
layout (location = 1) in vec3 normal;
layout (location = 2) in vec3 color;
layout (location = 3) in vec2 uv;

out vec3 in_color;
out vec2 in_uv;

vec3 apply_lights(vec3 material_color) {
    vec3 ret_color = material_color * ambient_color;
    vec3 normal = normalize(normal);

    for (int i = 0; i < lights_amount; ++i) {
        vec3 light_position = light_positions[i];
        vec3 light_color = light_colors[i];
        float light_radius = light_radiuses[i];
        float light_luminosity = light_luminosities[i];

        float light_dist = distance(light_position, position);
        vec3 light_dir = normalize(position-light_position);
        float dt = max(dot(normal, light_dir), 0);

        ret_color += light_color*dt*(clamp(light_radius/pow(light_dist+1, 2), 0, light_luminosity));
    }

    return ret_color;
}

void main() {
    vec3 pos = camera_rot*(position-camera_pos);
    gl_Position = projection*(vec4(pos, 1));

    in_color = apply_lights(color);
    in_uv = vec2(uv.x/texture_size.x, uv.y/texture_size.y);
}  