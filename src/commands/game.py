import trueskill
from discord import ApplicationContext, User
from commands.queue import QUEUE
from typing import List, Dict
import numpy as np
from itertools import combinations
from scipy.optimize import linear_sum_assignment


def convert_int_to_role(role_int: int) -> str:
    if role_int == 0 or role_int == 1:
        return "Tanks"
    elif role_int == 2 or role_int == 3:
        return "Supports"
    elif role_int == 4 or role_int == 5 or role_int == 6 or role_int == 7:
        return "Assassins"
    elif role_int == 8 or role_int == 9:
        return "Offlanes"


def create_game(ctx: ApplicationContext) -> None:
    players_in_queue: List[User] = QUEUE.copy()
    player_set = set(players_in_queue)
    combinations_of_players: List[List[User]] = [
        list(comb) for comb in combinations(player_set, 10)
    ]
    valid_games = []

    # For each player in the queue, create a numpy matrix, where the rows are the players, and the columns are the roles (Tank, Healer, Assassin, Offlane).
    # The cost of each player to be assigned to a role is 0 if they have the role, 1 if they are a fill, and 2 if they do not have any roles.
    for perm in combinations_of_players:
        matrix = np.full((len(perm), 10), 2)
        for i, player in enumerate(perm):
            for role in player.roles:
                if role.name == "Tank":
                    matrix[i][0] = 0
                    matrix[i][1] = 0
                elif role.name == "Tank (Fill)":
                    matrix[i][0] = 1
                    matrix[i][1] = 1
                elif role.name == "Support":
                    matrix[i][2] = 0
                    matrix[i][3] = 0
                elif role.name == "Support (Fill)":
                    matrix[i][2] = 1
                    matrix[i][3] = 1
                elif role.name == "Assassin":
                    matrix[i][4] = 0
                    matrix[i][5] = 0
                    matrix[i][6] = 0
                    matrix[i][7] = 0
                elif role.name == "Assassin (Fill)":
                    matrix[i][4] = 1
                    matrix[i][5] = 1
                    matrix[i][6] = 1
                    matrix[i][7] = 1
                elif role.name == "Offlane":
                    matrix[i][8] = 0
                    matrix[i][9] = 0
                elif role.name == "Offlane (Fill)":
                    matrix[i][8] = 1
                    matrix[i][9] = 1
        # Find the optimal matching
        row_ind, col_ind = linear_sum_assignment(matrix)
        # Check if this is a valid set, if not, continue to the next 10 perm.
        if any(matrix[row_ind, col_ind] == 2):
            continue
        game_dict = {"Tanks": [], "Supports": [], "Assassins": [], "Offlanes": []}
        for i, player in enumerate(perm):
            game_dict[convert_int_to_role(col_ind[i])].append(player)
        valid_games.append(game_dict)

    # Use the hungarian algorithm to solve the assignment problem.
