## Plan
1. Create a basic game plan
2. Priority for systems (systems get sorted at the end, based on their priority)
3. Sprite text rendering (text that will be rendered similar to sprites) 
4. Basic scene support (main menu, ingame, ...) 
5. Model a simple UDP network protocol, that would feature reliability, data integrity checks and dublicate avoidance.
6. Add a basic multiplayer support (no anticheat for now)
7. Add lighting to the game
...
10. Find assets like music, sounds, textures and fonts for the game. Learn more about license merging 

... More to see 

## Server architecture
While the messaging approach is yet no clear (how to pass messages: using an RPC architecture or events?)
The general idea though that since the game is always played in LAN multiplayer - there's no reason to 
make a separate, bare minimum version of the game. What we do need, is just a separation of responsibilities:

The server executes game logic, and the client interpolates and acts on it. 
We can achieve this using conditional systems (for example using a `@server` decorator), that will be run
ONLY if it's the server. They will transform a function so that it first performs a slight check, and if
it's true - execute the main system. If not - simply return.
This way, we can clearly separate the client logic (that should be the same for everyone, including the
server-player), while also providing additional logic.

In terms of data passing however, I think an event system could be pretty useful. Say, if on the server we would
like to change the position of the player - we would ideally send a specific event for that, like `PlayerMove`,
which will have new player coordinates and velocity.
But to send this event, we would need a separate service. We could make a `RemoteWriter` object, that would essentially collect all events and then retransmit them to remove receivers (either to other players or 
the host itself). 

Since `RemoteWriter` is "class" (idk, be it a client or a server) agnostic, it will feature functionality for
both the client and the server.

It's unclear for now what `RemoteWriter` should essentially be, but for now it could be a middleware between a 
socket server or a socket client. One thing that's known however, is that it should know whether it is a server or a client. As well, it should know whether a message is forwarded to the server, or a client.
The reasoning behind this decision is that a server sending a message to itself doesn't make any sense: it should
ideally get simply applied back on the next tick. However, a message sent from the server to a client has to result
in a message forwarding operation, and upon arival to the client - applying.

Thus, it means we need an actor-agnostic retransmitor, that would simply apply the changes itself whenever the
retransmitor sends messages to itself. There will be some assertion checks though, since it should be made
clear that a client can't possibly send a message to an another client, or some other unplanned BS.

The messages that get passed will also need to be serialized 