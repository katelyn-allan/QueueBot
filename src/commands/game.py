import trueskill
from discord import ApplicationContext, User
from commands.queue import QUEUE
from commands.player_stats import PLAYER_DATA
from typing import List, Dict
import numpy as np
from itertools import combinations
from scipy.optimize import linear_sum_assignment
import itertools


def convert_int_to_role(role_int: int) -> str:
    if role_int == 0 or role_int == 1:
        return "tank"
    elif role_int == 2 or role_int == 3:
        return "support"
    elif role_int == 4 or role_int == 5 or role_int == 6 or role_int == 7:
        return "assassin"
    elif role_int == 8 or role_int == 9:
        return "offlane"


class Player(User):
    def __init__(self, user: User, role: str):
        super().__init__(user.id, user.name, user.discriminator, user.avatar)
        self.role = role
        self.rating = PLAYER_DATA[str(user.id)][role]["rating"]


def find_valid_games() -> List[List[Player]]:
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
        game_dict = {"tank": [], "support": [], "assassin": [], "offlane": []}
        for i, player in enumerate(perm):
            game_dict[convert_int_to_role(col_ind[i])].append(player)
        valid_games.append(game_dict)

    return valid_games


def get_team_combinations(players: Dict[str, List[Player]]) -> List[List[List[Player]]]:
    """
    Finds every combination of players by role and returns a list of unique two team combinations.
    """
    combinations = []
    for tank in players["tank"]:
        for support in players["support"]:
            for assassin in itertools.combinations(players["assassin"], 2):
                for offlane in players["offlane"]:
                    combinations.append(
                        [tank, support, assassin[0], assassin[1], offlane]
                    )
    two_teams = []
    for team1 in combinations:
        for team2 in combinations:
            if not any(player in team2 for player in team1):
                if [team2, team1] not in two_teams:
                    two_teams.append([team1, team2])
    return two_teams


def balance_teams(valid_games: List[Dict[str, List[Player]]]) -> Dict[str, List[User]]:
    # For each game, calculate the average trueskill of each team. The team with the higher average trueskill is the better team.
    # Find the game with the smallest difference in average trueskill between the teams.
    # Return the game with the smallest difference in average trueskill between the teams.
    best_game = None
    best_diff = 10000
    for game in valid_games:
        # Find every permutation of team comp, in which a valid team has 5 players: One tank, One Support, Two Assassins, and One Offlane.
        team_combos: List[List[List[Player]]] = get_team_combinations(game)
