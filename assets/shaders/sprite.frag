#version 330 core

out vec4 FragColor;

uniform sampler2D material;

in vec2 in_uv;
in vec3 in_color;

void main()
{
    vec4 color = texture(material, in_uv);
    if (color.a < 0.1) {
        discard;
    }
    FragColor = color * vec4(in_color, 1);
}