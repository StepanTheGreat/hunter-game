#version 330 core

out vec4 FragColor;

uniform sampler2D material;

in vec2 in_uv;

void main()
{
    vec4 color = texture(material, in_uv);
    if (color.a < 0.1) {
        discard;
    }
    FragColor = color;
}