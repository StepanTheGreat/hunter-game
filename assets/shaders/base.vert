#version 330 core

const float LIGHT_RADIUS = 600;

uniform mat4 projection;
uniform mat3 camera_rot;
uniform vec3 camera_pos;

layout (location = 0) in vec3 position;
layout (location = 1) in vec3 color;
// Texture coordinates
layout (location = 2) in vec2 uv;

out vec3 in_color;
out vec2 in_uv;

void main()
{
    vec3 pos = camera_rot*(position-camera_pos);
    gl_Position = projection*(vec4(pos, 1));

    in_color = color * 1-clamp(0, distance(position, camera_pos)/LIGHT_RADIUS, 1);
    in_uv = uv;
}  