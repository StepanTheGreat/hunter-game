#version 330 core

out vec4 FragColor;
  
in vec3 in_color;

void main()
{
    FragColor = vec4(in_color, 1.0);
}