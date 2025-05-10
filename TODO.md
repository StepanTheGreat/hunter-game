## Temporary TODO
This project needs some really important refactoring changes:

### Consider using scenes on both the server and client
Scene bundles can be highly useful when managing state transitions, especially both on the client
and server. Making it a core plugin could be valuable for better state management.
One note though - scenes should only manipulate existing services and create application's flow. They
absolutely shouln't create their own services or state, like for example with the minimap and map
renderer... These should be services instead, not bound to any specific state...