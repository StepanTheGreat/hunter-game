#version 330 core

out vec4 FragColor;

uniform sampler2D material;

in vec3 in_color;
in vec2 in_uv;

void main()
{
    FragColor = texture(material, in_uv) * vec4(in_color, 1);
}