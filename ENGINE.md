## This file was created to share some thoughts on engine design and my current decision making.
Designing a good engine is hard. And apparently, no game engine is perfect either.

My current approach is using a pure plugin-system that's extremely common in ECS frameworks. It actually works
fine for core stuff like graphics, assets or game runners, as it decouples everything into small packages
that can be connected and run separately. Messages are passed either through directly accessing a service,
or through sending events, though the former is used way more frequently.

What are my thoughts on this? Well, for the cases I just described - it works absolutely awesome. An ability to
freely add new plugins, systems, resources and so on makes it ideal for core systems.
Asset management made it EXTREMELY convenient to just add new asset loaders and simplify the architecture by
orders of magnitude.

This however, has its own downsides - it's global state. Plugins are awesome for global state management and
services, but for tight-coupled state... It's fairly difficult. This is where the problems start to appear...

### Scenes
So, in a global state... how do you design local state? That is also easy to maintain and scale? I don't have 
an easy answer for that. Sometimes it's unclear what things should be global and what shouldn't. 
Sure, `AssetManager` or `InputManager` are core parts of everything, but say `NetworkManager`...? `NetworkController`?
It especially starts to get difficult when we have things like entities, that... tend to ask for a lot of stuff
outside of their reach, like entities that would like to get other entities via `EntityManager`. So, `EntityManager`
should be a global or local state? And I mean, what about `NetworkManager`? What happens when we leave the main
game to the main menu? We would need to separately disable it.

There are limitless problems with global state overall. And it's unclear what should be done about it.

Did I mention the performance of Python? Sure, this plugin/systems system would run perfectly in Golang or even 
better in non-GC languages, but... Python? Every single call is extremely expensive. We can't just waste those!
Sure, I didn't yet hit a hard wall with the current approach, but if I do - there's not much left to do, since
there are simmply a lot of systems that get run every single frame.

Well, there are a lot of problems as you get it.

### Possible solutions
Here I'll be maintatining possible solutions and ideas for mitigating this problem 

#### Scene bundles
The essential idea is really similar to what we have already been doing using Plugins, but this is more of a dynamic
approach - a dynamic bundle. As an ordinary plugin, a scene bundle would simply include a constant set of 
resources. 

When we would like to say, switch to a scene - we will insert our scene bundle into a `SceneManager`.
All of the bundle's resources will be inserted into the application, and thus our systems will be able to work
properly. 

One rule for this to succeed better, is to make all plugins care only about their state. Instead of checking
in a minimap plugin if the scene is ingame - we should ideally not care about the current scene at all - the only
thing we care about is rendering the minimap what it's present. If it's not - we aren't doing anything.
This way, all the composition happens at the scene-level, not component-level.

A few issues with this approach though:
1. We need to clean the previous scene bundle and its resources (Could be done via `SceneManager`)
2. The systems that operate on conditional resources (like say, rendering a map) have to be run conditionally.
Either through an ugly `if Resource not in resources: return` check, or a `@run_if(contains_resource, Resource)`
system decorator. The latter introduces 2 additional function calls per every system call.

#### Scene classes
We could take on a more OOP approach and simply abstract scenes as classes. We will no longer use systems
as our functionality drivers, and instead, all our functionality will be abstracted as modules included inside
other modules (compared to our previous approach, where every single plugin works independently of each other).

This introduces tight coupling, but makes it simple to manage state. Sort of... Some things still need global state,
like say entities that would like to get rendered and so on. It does make it a bit more performant (though not
guaranteed to be) in terms of amount of calls, but this tight coupling makes it really difficult to inner components
to interact with services outside. Unless we pass the resources to everyone and anything of course.

### Naming convetions
Since networking started being introduced, the whole naming conventions gone to hell. Nothing has any 
clear naming rules and everything has an arbitrary name. This paragaph will try to introduce and
standardize some notions around the project:
- **Action** (a remote action executed on the other end). If a client would like to move its character
on the server - they're doing an *action*. The same applies vice-versa.
- **Command** (an action initiated locally by the inner-systems). An RPC receiving a request to spawn
a player, when executed on the receiving end (in this case the client) gets elevated to a command. It's
not an action between 2 remotes - it's an action between to inner-system communicating with each other.
A command is a required action.
- **Event** (an occurence of something). 2 colliders colliding is an event. It's a description of an
existing action happening. It's however **is not an action**, only the reaction of said action.
- **RPC** (a Remote Procedure Call, a direct network port for a message). A server sending "hello" to
clients will mean that the clients would need a receiving port `hello`, and the server having the sending
<<<<<<< HEAD
port `hello`. An RPC is a direct transport layer if you would say.
=======
port `hello`. An RPC is a direct transport layer if you would say.

### Network communication
This simple guide is going to introduce you to how you can register new endpoints, receive network
commands and so on.
For this, we will use 3 key concepts from our naming convention: an action, a command and RPC.

#### Sending data
To invoke a command, we use **actions**. Actions store all required information to execute our RPCs,
such as RPC function, arguments, to which address (if it's a server action) and so on. Actions
can be dispatched using `ActionDispatcher` on a respected network actor, and these are then
immediately dispatched into RPCs.

The reason why we're using actions is because it allows us to abstract parsing and direct
RPC interactions into a simple "action-based` system. So, if you would like to pass some command/action - 
first create an appropriate action for it.

#### Receiving data
Receiving data takes a lot more steps.
First we need to setup an RPC, the "physical port", to which our data will arrive. Without it
it will be impossible to receive the data in the first place.
RPC can handle all the parsing logic.

Then, when setup, we need to create a proper `Command` structure for this same RPC. A command is 
essentially a transfered `Action`. A command can also be used to inter-communicate between systems
in a usual workflow, so it suits our usecase here.
A command should represent the most important data for said action, and be dispatched
via `EventWriter`, so that systems can listen to it and react.


And essentially, that's it.
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
