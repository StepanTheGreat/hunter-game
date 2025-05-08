## Temporary TODO
This project needs some really important refactoring changes:

### Events/Commands
Events and commands should be centralized throughout the codebase. Right now different domains
declare their own events/commands **with** domain logic. This shouldn't really be the case, as
this create tight coupling. Why would I push events to say a light service, if I import it directly
anyway? This leads to highly confusing setups, naming and so on.
Ideally, both of these should be separated into their own directories as well. Something like
`events` and `commands`. For more domain specificity, one could also create inner `session` (session events) and `rpc` (rpc commands) and so on. This is overall a tons more clear than having it thrown
around in the codebase.

This however doesn't mean that EVERYTHING should be abstracted into events/commands -  only parts that
benefit from it. Things like direct rendering for example requires direct service access, and there's
nothing wrong with that. In any other case it should be separated in a structure above.

### Components
It makes absolutely zero sense to put these into domain specific code... Components should be
centralized... And component definitions shouldn't contain logic!! 
While it is already somewhat the case around the codebase - some extremely stupid components in graphics
or entities still exist. They make ZERO SENSE.

Put it into domain-specific sub-modules **inside** components, like `components/player`

### Systems
So now that components are separated into a separate `components` module, all general logic 
should now exist in a separate `systems` module. Essentially the same thing, domain-specific
submodules are allowed and even are recommended. One thing is that throughout the codebase
there will be some highly coupled code, for example in services. In these specific cases it
would be highly complex to manage such centralized systems, so services are an exception to this
for now.

### Services
As mentioned previously, systems are by design extremely coupled, but coupled locally, so they're
allowed as their own plugins with their own systems/resources and so on. (Except for events or components - nope`)