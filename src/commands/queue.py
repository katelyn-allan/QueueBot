from discord import ApplicationContext
from typing import List, Dict
from dotenv import load_dotenv
from role_ids import *

load_dotenv()


QUEUE: List[int] = []


def join_queue(ctx: ApplicationContext) -> tuple([int, int]):
    """Facilitates joining the queue, returns the user's id and the number of people in the queue"""
    user_id = ctx.user.id
    QUEUE.append(user_id)
    return user_id, len(QUEUE)


def get_queue_data(ctx: ApplicationContext, queue=QUEUE) -> list:
    """Lists the players in the queue and their roles"""
    # For each User in the queue list their roles in the current guild
    queue_data = {
        "Tanks": [],
        "Supports": [],
        "Assassins": [],
        "Offlaners": [],
        "Tanks (Fill)": [],
        "Supports (Fill)": [],
        "Assassins (Fill)": [],
        "Offlaners (Fill)": [],
    }
    for user_id in queue:
        # For each of the user's roles that match the list in queue_data, append the user's name to the list, with (Fill) if they're a fill
        for role in ctx.guild.get_member(user_id).roles:
            if role.id == TANK_ID:
                queue_data["Tanks"].append(user_id)
            if role.id == SUPPORT_ID:
                queue_data["Supports"].append(user_id)
            if role.id == ASSASSIN_ID:
                queue_data["Assassins"].append(user_id)
            if role.id == OFFLANE_ID:
                queue_data["Offlaners"].append(user_id)
            if role.id == TANK_FILL_ID:
                queue_data["Tanks (Fill)"].append(user_id)
            if role.id == SUPPORT_FILL_ID:
                queue_data["Supports (Fill)"].append(user_id)
            if role.id == ASSASSIN_FILL_ID:
                queue_data["Assassins (Fill)"].append(user_id)
            if role.id == OFFLANE_FILL_ID:
                queue_data["Offlaners (Fill)"].append(user_id)

    return queue_data


def get_nickname_from_id(ctx: ApplicationContext, user_id: int) -> str:
    """Returns the nickname of the user with the given id"""
    return ctx.guild.get_member(user_id).nick


def create_adjusted_list(
    key: str, ctx: ApplicationContext, queue_data: Dict[str, List[int]]
):
    """Creates an adjusted list by combining the role and fill lists"""
    return [get_nickname_from_id(ctx, u_id) for u_id in queue_data[key]] + [
        get_nickname_from_id(ctx, u_id) + " (Fill)"
        for u_id in queue_data[key + " (Fill)"]
    ]


def list_queue(ctx: ApplicationContext) -> str:
    """Lists the players in the queue"""
    queue_data: Dict[str, List[int]] = get_queue_data(ctx)
    # Create adjusted lists by combining the role and fill lists
    adjusted_queue_data = {
        "Tanks": create_adjusted_list("Tanks", ctx, queue_data),
        "Supports": create_adjusted_list("Supports", ctx, queue_data),
        "Assassins": create_adjusted_list("Assassins", ctx, queue_data),
        "Offlaners": create_adjusted_list("Offlaners", ctx, queue_data),
    }
    return adjusted_queue_data


def leave_queue(ctx: ApplicationContext) -> tuple([int, int]):
    """Facilitates leaving the queue, returns the user's id and the number of people in the queue"""
    user_id = ctx.user.id
    QUEUE.remove(user_id)
    return user_id, len(QUEUE)


def clear_queue() -> None:
    """Clears the queue"""
    QUEUE.clear()
