#version 330 core

const float QUALITY = 8;

out vec4 FragColor;
uniform sampler2D screen;

in vec2 in_uv;

void main()
{
    vec4 color = texture(screen, in_uv);
    FragColor = color;
}  