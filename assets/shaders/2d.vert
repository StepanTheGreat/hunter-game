#version 330 core

uniform mat4 projection;
uniform vec2 texture_size;

layout (location = 0) in vec2 position;
layout (location = 1) in vec3 color;
layout (location = 2) in vec2 uv;

out vec3 in_color;
out vec2 in_uv;

void main()
{
    gl_Position = projection*(vec4(position, 0, 1));

    in_color = color;
    in_uv = vec2(uv.x/texture_size.x, uv.y/texture_size.y);
}  