import trueskill
from discord import ApplicationContext, User
from commands.queue import QUEUE
from typing import List, Dict
import numpy as np


# Implement the hungarian algorithm to solve the assignment problem,
# where we're maximizing cost to assign users in the queue to a 5 man team,
# where each user has a cost to be assigned to a role, and a team has a tank, a support, two assassins, and an offlane.
# If a player has the discord role for their game role, they have a cost of 2, if they are listed as a fill, it is a cost of 1, and if they do not have any roles associated, it is a cost of 0.


def create_game(ctx: ApplicationContext) -> None:
    players_in_queue = QUEUE.copy()
