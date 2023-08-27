from discord import ApplicationContext, Member, Guild
from typing import List, Dict, Self, Tuple, Type
from dotenv import load_dotenv
from util.env_load import (
    ASSASSIN_FILL_ID,
    ASSASSIN_ID,
    OFFLANE_FILL_ID,
    OFFLANE_ID,
    QUEUED_ID,
    SUPPORT_FILL_ID,
    SUPPORT_ID,
    TANK_FILL_ID,
    TANK_ID,
)

from util.exceptions import (
    AlreadyInQueueException,
    ChannelNotFoundException,
    NoGuildException,
    NoMainRoleException,
    PlayerNotFoundException,
)

import logging

logger = logging.getLogger(__name__)

load_dotenv()


class Queue:
    """Singleton class to represent the queue."""

    def __new__(cls: Type["Queue"]) -> "Queue":
        """Create a new instance of the queue."""
        if not hasattr(cls, "instance"):
            cls.instance = super(Queue, cls).__new__(cls)
            cls.instance.initialized = False
        return cls.instance

    def __init__(self: Self) -> None:
        """Initialize the queue."""
        if hasattr(self, "initialized") and self.initialized:
            return
        else:
            self.initialized = True
            self.queue: List[Member] = []

    def as_dict(self: Self) -> Dict[str, List[str]]:  # noqa: C901
        """Lists the players in the queue and their roles."""
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
        for user in self.queue:
            # For each of the user's roles that match the list in queue_data,
            # append the user's name to the list, with (Fill) if they're a fill
            name = user.display_name if user.display_name else user.name
            for role in user.roles:
                role_id = role.id
                if role_id == TANK_ID:
                    queue_data["Tanks"].append(name)
                elif role_id == SUPPORT_ID:
                    queue_data["Supports"].append(name)
                elif role_id == ASSASSIN_ID:
                    queue_data["Assassins"].append(name)
                elif role_id == OFFLANE_ID:
                    queue_data["Offlanes"].append(name)
                elif role_id == TANK_FILL_ID:
                    queue_data["Tanks (Fill)"].append(name)
                elif role_id == SUPPORT_FILL_ID:
                    queue_data["Supports (Fill)"].append(name)
                elif role_id == ASSASSIN_FILL_ID:
                    queue_data["Assassins (Fill)"].append(name)
                elif role_id == OFFLANE_FILL_ID:
                    queue_data["Offlanes (Fill)"].append(name)

        return queue_data

    def join_queue(self: Self, ctx: ApplicationContext) -> Tuple[int, int]:
        """Facilitates joining the queue, returns the user's id and the number of people in the queue."""
        assert type(ctx.user) is Member
        if ctx.user in self.queue:
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
        self.queue.append(ctx.user)
        # Assign the user the queued role

        return ctx.user.id, len(self.queue)

    def leave_queue(self: Self, ctx: ApplicationContext) -> Tuple[int, int]:
        """Facilitates leaving the queue, returns the user's id and the number of people in the queue."""
        if ctx.user not in self.queue:
            raise PlayerNotFoundException(ctx.user)
        self.queue.remove(ctx.user)

        return ctx.user.id, len(self.queue)

    def remove_from_queue(self: Self, user: Member) -> Tuple[int, int]:
        """Removes a player from the queue."""
        if user not in self.queue:
            raise PlayerNotFoundException(user)
        self.queue.remove(user)

        return user.id, len(self.queue)


def populate_queue(guild: Guild) -> int:
    """Populates the queue with all players who have the Queued Role."""
    if guild is None:
        raise NoGuildException
    queued_role = guild.get_role(QUEUED_ID)
    for member in guild.members:
        if queued_role in member.roles:
            Queue().queue.append(member)
    len_queue = len(Queue().queue)
    logger.info(f"Queue initialized with {len_queue}")
    return len_queue

