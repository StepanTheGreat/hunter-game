#version 330 core

// We have only 4 faces, 4 verticies per each, thus 16 UV coordinates in total
const int SKYBOX_UV_COORDINATES = 16;

uniform mat4 projection;
uniform mat3 camera_rot;
uniform vec2 texture_size;

uniform vec3 skybox_color;
uniform vec2[SKYBOX_UV_COORDINATES] skybox_uvs;

layout (location = 0) in vec3 position;
layout (location = 1) in uint uv_ind;

out vec3 in_color;
out vec2 in_uv;

void main() {

    vec4 in_pos = projection*vec4(camera_rot*position, 1);

    // This trick is from https://learnopengl.com/Advanced-OpenGL/Cubemaps
    // essentially this is what forces our skybox to always have the maximum depth, thus getting
    // hiden by other objects in the scene
    gl_Position = in_pos;

    vec2 uv = skybox_uvs[uv_ind];
    in_uv = vec2(uv.x/texture_size.x, uv.y/texture_size.y);
    in_color = skybox_color;
}  