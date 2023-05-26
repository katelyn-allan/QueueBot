from discord import ApplicationContext, User
from typing import List, Dict
from dotenv import load_dotenv
from role_ids import *
from exceptions import *

load_dotenv()


QUEUE: List[User] = []


def join_queue(ctx: ApplicationContext) -> tuple([int, int]):
    """Facilitates joining the queue, returns the user's id and the number of people in the queue"""
    if ctx.user in QUEUE:
        raise AlreadyInQueueException(ctx.user)
    QUEUE.append(ctx.user)
    return ctx.user.id, len(QUEUE)


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
    for user in queue:
        # For each of the user's roles that match the list in queue_data, append the user's name to the list, with (Fill) if they're a fill
        for role in user.roles:
            if role.id == TANK_ID:
                queue_data["Tanks"].append(user.nick)
            if role.id == SUPPORT_ID:
                queue_data["Supports"].append(user.nick)
            if role.id == ASSASSIN_ID:
                queue_data["Assassins"].append(user.nick)
            if role.id == OFFLANE_ID:
                queue_data["Offlaners"].append(user.nick)
            if role.id == TANK_FILL_ID:
                queue_data["Tanks (Fill)"].append(user.nick)
            if role.id == SUPPORT_FILL_ID:
                queue_data["Supports (Fill)"].append(user.nick)
            if role.id == ASSASSIN_FILL_ID:
                queue_data["Assassins (Fill)"].append(user.nick)
            if role.id == OFFLANE_FILL_ID:
                queue_data["Offlaners (Fill)"].append(user.nick)

    return queue_data


def create_adjusted_list(key: str, queue_data: Dict[str, List[int]]):
    """Creates an adjusted list by combining the role and fill lists"""
    return queue_data[key] + queue_data[key + " (Fill)"]


def list_queue(ctx: ApplicationContext) -> str:
    """Lists the players in the queue"""
    queue_data: Dict[str, List[int]] = get_queue_data(ctx)
    # Create adjusted lists by combining the role and fill lists
    adjusted_queue_data = {
        "Tanks": create_adjusted_list("Tanks", queue_data),
        "Supports": create_adjusted_list("Supports", queue_data),
        "Assassins": create_adjusted_list("Assassins", queue_data),
        "Offlaners": create_adjusted_list("Offlaners", queue_data),
    }
    return adjusted_queue_data


def leave_queue(ctx: ApplicationContext) -> tuple([int, int]):
    """Facilitates leaving the queue, returns the user's id and the number of people in the queue"""
    if ctx.user not in QUEUE:
        raise PlayerNotFoundException(ctx.user)
    QUEUE.remove(ctx.user)
    return ctx.user.id, len(QUEUE)


def clear_queue() -> None:
    """Clears the queue"""
    QUEUE.clear()
