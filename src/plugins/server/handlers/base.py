from plugin import Plugin, Resources

from core.ecs import WorldECS

from plugins.server.events import RemovedNetworkEntityEvent
from plugins.server.components import *

from plugins.rpcs.server import ControlPlayerCommand

from plugins.server.actions import *

from plugins.server.services.clientlist import ClientList

from plugins.shared.constants import SNAP_PLAYER_POSITION_DISTANCE


def on_control_player_command(resources: Resources, command: ControlPlayerCommand):
    world = resources[WorldECS]
    clientlist = resources[ClientList]

    if not clientlist.contains_client_addr(command.addr):
        return

    client_ent = clientlist.get_client_ent(command.addr)

    if not world.has_component(client_ent, OwnsEntity):
        return

    player_ent = world.get_component(client_ent, OwnsEntity).get_ent()
    
    if not world.contains_entity(player_ent):
        return

    pos, vel, angle, angle_vel, controller = world.get_components(
        player_ent, 
        Position, 
        Velocity, 
        Angle, 
        AngleVelocity,
        PlayerController
    )

    # If the distance between server-side position and player's position is less than
    # the stap distance - we're going to accept its movement packet
    new_pos = command.pos
    if pos.get_position().distance_to(new_pos) <= SNAP_PLAYER_POSITION_DISTANCE:
        pos.set_position(*new_pos)

    vel.set_velocity(*command.vel)
    angle.set_angle(command.angle)
    angle_vel.set_velocity(command.angle_vel)

    controller.is_shooting = command.is_shooting

def on_network_entity_removal(resources: Resources, event: RemovedNetworkEntityEvent):
    """
    When a network entity gets removed from the ECS world, we would like to push an
    action notifying all other clients of this removal.
    """

    world = resources[WorldECS]
    action = resources[ServerActionDispatcher]

    ent = event.ent
    uid = event.uid
    comps = event.comps

    if OwnedByClient in comps:
        # If this network entity was owned by the client - we're going to 
        # iterate all our existing clients who own an entity and check their bound entity id.
        # If it matches - we're going to remove the component from them


        # We use a command buffer because we're modifying components while iterating
        with world.command_buffer() as cmd:

            # We only query clients who own an entity
            for client_ent, owned_ent in world.query_component(OwnsEntity):
                
                # If entity IDS match - we're going to remove the owning compononent
                if owned_ent.get_ent() == ent:
                    cmd.remove_components(client_ent, OwnsEntity)
    
    # In any other case, we're dispatching the global removal of said entity by its UID
    action.dispatch_action(KillEntityAction(uid))

class BaseHandlersPlugin(Plugin):
    def build(self, app):
        app.add_event_listener(ControlPlayerCommand, on_control_player_command)
        app.add_event_listener(RemovedNetworkEntityEvent, on_network_entity_removal)