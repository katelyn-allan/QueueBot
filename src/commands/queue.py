from discord import ApplicationContext, User
from typing import List, Dict
from dotenv import load_dotenv
from role_ids import *
from exceptions import *

load_dotenv()


QUEUE: List[User] = []


def populate_queue(ctx: ApplicationContext) -> None:
    """Populates the queue with all players who have the Queued Role"""
    queued_role = ctx.guild.get_role(QUEUED_ID)
    for member in ctx.guild.members:
        if queued_role in member.roles:
            QUEUE.append(member)
    print(f"Queue initialized with {len(QUEUE)}")
    return len(QUEUE)


async def update_queue_channel(ctx: ApplicationContext, queue_length: int) -> None:
    """Updates the queue channel with the current queue"""
    queue_channel = ctx.guild.get_channel(QUEUE_INFO_CHANNEL_ID)
    plural = "s" if queue_length != 1 else ""

    print(queue_channel)
    # Rename the queue channel to display the queue
    await queue_channel.edit(name=f"QUEUE | {queue_length} player{plural}")
    print("Successfully updated the queue channel")


def join_queue(ctx: ApplicationContext) -> tuple([int, int]):
    """Facilitates joining the queue, returns the user's id and the number of people in the queue"""
    if ctx.user in QUEUE:
        raise AlreadyInQueueException(ctx.user)
    # Raise an error if the user does not have a main role set
    user_roles = [role.id for role in ctx.user.roles]
    if (
        TANK_ID not in user_roles
        and SUPPORT_ID not in user_roles
        and ASSASSIN_ID not in user_roles
        and OFFLANE_ID not in user_roles
    ):
        raise NoMainRoleException(ctx.user)
    QUEUE.append(ctx.user)
    # Assign the user the queued role

    return ctx.user.id, len(QUEUE)


def get_queue_data(
    ctx: ApplicationContext, queue: List[User] = QUEUE
) -> Dict[str, List[str]]:
    """Lists the players in the queue and their roles"""
    # For each User in the queue list their roles in the current guild
    queue_data = {
        "Tanks": [],
        "Supports": [],
        "Assassins": [],
        "Offlanes": [],
        "Tanks (Fill)": [],
        "Supports (Fill)": [],
        "Assassins (Fill)": [],
        "Offlanes (Fill)": [],
    }
    for user in queue:
        # For each of the user's roles that match the list in queue_data, append the user's name to the list, with (Fill) if they're a fill
        name = user.display_name if user.display_name else user.name
        for role in user.roles:
            if role.id == TANK_ID:
                queue_data["Tanks"].append(name)
            if role.id == SUPPORT_ID:
                queue_data["Supports"].append(name)
            if role.id == ASSASSIN_ID:
                queue_data["Assassins"].append(name)
            if role.id == OFFLANE_ID:
                queue_data["Offlanes"].append(name)
            if role.id == TANK_FILL_ID:
                queue_data["Tanks (Fill)"].append(name)
            if role.id == SUPPORT_FILL_ID:
                queue_data["Supports (Fill)"].append(name)
            if role.id == ASSASSIN_FILL_ID:
                queue_data["Assassins (Fill)"].append(name)
            if role.id == OFFLANE_FILL_ID:
                queue_data["Offlanes (Fill)"].append(name)

    return queue_data


def leave_queue(ctx: ApplicationContext) -> tuple([int, int]):
    """Facilitates leaving the queue, returns the user's id and the number of people in the queue"""
    if ctx.user not in QUEUE:
        raise PlayerNotFoundException(ctx.user)
    QUEUE.remove(ctx.user)

    return ctx.user.id, len(QUEUE)


def clear_queue() -> None:
    """Clears the queue"""
    QUEUE.clear()


def remove_from_queue(user: User) -> tuple([int, int]):
    """Removes a player from the queue"""
    if user not in QUEUE:
        raise PlayerNotFoundException(user)
    QUEUE.remove(user)

    return user.id, len(QUEUE)
