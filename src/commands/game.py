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
    # For each player in the queue, create a numpy matrix, where the rows are the players, and the columns are the roles (Tank, Healer, Assassin, Offlane).
    # The cost of each player to be assigned to a role is 2 if they have the role, 1 if they are a fill, and 0 if they do not have any roles.
    matrix = np.zeros((len(players_in_queue), 4))
    for i, player in enumerate(players_in_queue):
        for j, role in enumerate(player.roles):
            if role.name == "Tank":
                matrix[i][0] = 2
            elif role.name == "Healer":
                matrix[i][1] = 2
            elif role.name == "Assassin":
                matrix[i][2] = 2
            elif role.name == "Offlane":
                matrix[i][3] = 2
            elif role.name == "Fill":
                matrix[i][j] = 1
