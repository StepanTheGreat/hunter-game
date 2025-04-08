#version 330 core

const float LIGHT_RADIUS = 600;
const int LIGHT_LIMIT = 256;

struct Light {
    vec3 position;
    vec3 color;
};

uniform mat4 projection;
uniform mat3 camera_rot;
uniform vec3 camera_pos;

uniform Light[LIGHT_LIMIT] lights;
uniform int lights_amount;

layout (location = 0) in vec3 position;
layout (location = 1) in vec3 normal;
layout (location = 2) in vec3 color;
// Texture coordinates
layout (location = 3) in vec2 uv;

out vec3 in_color;
out vec2 in_uv;

void main() {
    vec3 pos = camera_rot*(position-camera_pos);
    gl_Position = projection*(vec4(pos, 1));

    in_uv = uv;
    in_color = color;

    if (lights_amount > 0) {
        Light light = lights[0];

        float camera_dist = distance(light.position, camera_pos);
        vec3 camera_dir = camera_pos-light.position;

        in_color *= light.color * (1-clamp(camera_dist/LIGHT_RADIUS*dot(normal, camera_dir), 0, 1));
    }
    // for (int i = 0; i < lights_amount; i++) {
    //     Light light = lights[i];

    //     float camera_dist = distance(light.position, camera_pos);
    //     vec3 camera_dir = camera_pos-light.position;

    //     in_color *= light.color * (1-clamp(camera_dist/LIGHT_RADIUS*dot(normal, camera_dir), 0, 1));
    // }
}  