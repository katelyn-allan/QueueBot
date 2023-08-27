import trueskill
from discord import ApplicationContext, Member
from commands.queue import QUEUE
from commands.player_stats import (
    PlayerData,
    RoleStat,
)
from typing import List, Dict, Self, Type
import numpy as np
import itertools
from scipy.optimize import linear_sum_assignment
import random
from util.env_load import ADMIN_ID, LOBBY_CHANNEL_ID, TEAM_1_CHANNEL_ID, TEAM_2_CHANNEL_ID

from util.exceptions import (
    CouldNotFindChannelException,
    GameInProgressException,
    NoGameInProgressException,
    NoGuildException,
    NoValidGameException,
    NotAdminException,
)
import logging

logger = logging.getLogger(__name__)


def convert_int_to_role(role_int: int) -> str:
    """Helper function which turns a cost matrix indicy into a role string."""
    if role_int == 0 or role_int == 1:
        return "tank"
    elif role_int == 2 or role_int == 3:
        return "support"
    elif role_int == 4 or role_int == 5 or role_int == 6 or role_int == 7:
        return "assassin"
    elif role_int == 8 or role_int == 9:
        return "offlane"
    else:
        raise Exception("Invalid role int")


class Player:
    """Class to store a player's role and rating for use in the game."""

    def __init__(self: Self, user: Member, role: str) -> None:
        """Init that takes in a user and role argument to create a Player object.

        Because the default User or Member class does not allow for role assignment, this class acts
        as a superclass of that more or less that allows for the role to be stored, along with the respective rating.
        """
        self.user = user
        self.role = role
        self.rating = getattr(PlayerData().player_data[str(user.id)], role).rating

    def report_player_data(self: Self, win: bool) -> None:
        """Updates the player's rating in the PLAYER_DATA dictionary."""
        player_data_obj: RoleStat = getattr(PlayerData().player_data[str(self.user.id)], self.role)
        logger.info(f"I think {self.user.display_name}'s player_data object is {player_data_obj}")
        player_data_obj.rating = self.rating
        player_data_obj.games_played += 1
        if win:
            player_data_obj.games_won += 1


class CurrentGame:
    """Singleton class to track the curent game.

    TODO: Store a list of active games if we allow multiple games to run.
    """

    # TODO: Make this configurable?
    valid_maps = [
        "Alterac Pass",
        "Garden of Terror",
        "Volskaya Foundry",
        "Towers of Doom",
        "Infernal Shrines",
        "Battlefield of Eternity",
        "Tomb of the Spider Queen",
        "Sky Temple",
        "Dragon Shire",
        "Cursed Hollow",
        # "Braxis Holdout",
    ]

    # Instantiate a singleton class, CurrentGame
    def __new__(cls: Type["CurrentGame"]) -> "CurrentGame":
        """Handle creation of a new class instance.

        Because this is a singleton, we only want to create one instance of this class,
        and return that same instance if a new one is attempted to be created after.
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(CurrentGame, cls).__new__(cls)
            cls.instance.initialized = False
        return cls.instance

    def __init__(self: Self) -> None:
        """Initialize this class instance."""
        if hasattr(self, "initialized") and self.initialized:
            return
        else:
            self.initialized = True
            self.reset_state()

    def assign_game(
        self: Self,
        team_1: Dict[str, Player],
        team_2: Dict[str, Player],
    ) -> None:
        """Assign the game to the active CurrentGame object."""
        self.team_1 = team_1
        self.team_2 = team_2
        self.map = random.choice(self.valid_maps)
        self.first_pick = random.choice([1, 2])
        self.in_progress = True

    def reset_state(self: Self) -> None:
        """Set the appropriate variables for a default state."""
        self.team_1 = {}
        self.team_2 = {}
        self.map = None
        self.first_pick = None
        self.in_progress = False


def find_valid_games() -> List[Dict[str, List[Player]]]:
    """
    Finds all valid games of 10 players from the queue.
    A valid game has: 2 tanks, 2 supports, 4 assassins, and 2 offlanes. Players are priotized onto their primary role.
    """
    players_in_queue: List[Member] = QUEUE.copy()
    PlayerData().instantiate_new_players(players_in_queue)
    player_set = set(players_in_queue)
    combinations_of_players: List[List[Member]] = [list(comb) for comb in itertools.combinations(player_set, 10)]
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
        # Find the optimal matching using the Hungarian Algorithm
        # https://docs.scipy.org/doc/scipy-0.18.1/reference/generated/scipy.optimize.linear_sum_assignment.html
        row_ind, col_ind = linear_sum_assignment(matrix)
        # Check if this is a valid set, if not, continue to the next 10 perm.
        if any(matrix[row_ind, col_ind] == 2):
            continue
        game_dict = {"tank": [], "support": [], "assassin": [], "offlane": []}
        for i, player in enumerate(perm):
            role = convert_int_to_role(col_ind[i])
            game_dict[role].append(Player(player, role))
        valid_games.append(game_dict)

    return valid_games


def get_team_combinations(players: Dict[str, List[Player]]) -> List[List[List[Player]]]:
    """Finds every combination of players by role and returns a list of unique two team combinations."""
    combinations = []
    for tank in players["tank"]:
        for support in players["support"]:
            for assassin in itertools.combinations(players["assassin"], 2):
                for offlane in players["offlane"]:
                    combinations.append([tank, support, assassin[0], assassin[1], offlane])
    two_teams = []
    for team1 in combinations:
        for team2 in combinations:
            if not any(player in team2 for player in team1):
                if [team2, team1] not in two_teams:
                    two_teams.append([team1, team2])

    random.shuffle(two_teams)
    random.shuffle(two_teams)
    random.shuffle(two_teams)
    return two_teams


def find_best_game(valid_games: List[Dict[str, List[Player]]]) -> Dict[str, Dict[str, Player] | str]:
    """Takes in a set of valid games, broken down by role, and returns the best game by trueskill rating calculation."""
    best_game = None
    best_quality = 10000
    for game in valid_games:
        # Find every permutation of team comp, in which a valid team has 5 players: One tank, One Support, Two Assassins, and One Offlane.
        team_combos: List[List[List[Player]]] = get_team_combinations(game)
        logger.info(f"Found {len(team_combos)} configurations of players for this game group")
        # TODO: Should we instead compare match quality within team_combos and then take a random game?
        for combo in team_combos:
            team1 = combo[0]
            team2 = combo[1]
            match_quality = trueskill.quality(
                [
                    [player.rating for player in team1],
                    [player.rating for player in team2],
                ]
            )
            # Check if match_quality is closer to 0.5 than the current best match_quality.
            if abs(0.5 - match_quality) < abs(0.5 - best_quality):
                best_game = combo
                best_quality = match_quality

    if best_game is None or valid_games == []:
        raise NoValidGameException("No valid game was found.")

    team1 = {}
    team2 = {}
    for player in best_game[0]:
        if player.role == "assassin" and "assassin" in team1:
            team1["assassin2"] = player
        else:
            team1[player.role] = player
    for player in best_game[1]:
        if player.role == "assassin" and "assassin" in team2:
            team2["assassin2"] = player
        else:
            team2[player.role] = player

    return {"team1": team1, "team2": team2}


async def start_game(ctx: ApplicationContext) -> bool:
    """Takes the players from the queue and creates a game."""
    assert type(ctx.user) is Member
    if ADMIN_ID in [role.id for role in ctx.user.roles] or ctx.user.guild_permissions.administrator:
        if CurrentGame().in_progress:
            raise GameInProgressException("A game is already in progress.")
        valid_games = find_valid_games()
        logger.info(f"Found {len(valid_games)} valid game configurations...")
        if len(valid_games) == 0:
            raise NoValidGameException("Not enough players on each role to make a valid game.")
        best_game = find_best_game(valid_games)
        CurrentGame().assign_game(best_game["team1"], best_game["team2"])
        for player in best_game["team1"].values():
            await move_player_from_lobby_to_team_voice(player.user, 1, ctx)
        for player in best_game["team2"].values():
            await move_player_from_lobby_to_team_voice(player.user, 2, ctx)
        return True
    else:
        raise NotAdminException("You must be an admin to start a game.")


async def move_player_from_lobby_to_team_voice(disc_user: Member, team_number: int, ctx: ApplicationContext):
    """Moves a player from the lobby voice channel to the Team 1 voice channel."""
    if ctx.guild is None:
        raise NoGuildException
    if team_number == 1:
        team_voice_channel = ctx.guild.get_channel(TEAM_1_CHANNEL_ID)
        channel_id = TEAM_1_CHANNEL_ID
    elif team_number == 2:
        team_voice_channel = ctx.guild.get_channel(TEAM_2_CHANNEL_ID)
        channel_id = TEAM_2_CHANNEL_ID
    else:
        raise Exception("Invalid team number")
    if team_voice_channel is None:
        raise CouldNotFindChannelException(f"Team {team_number} Voice Channel", channel_id)
    try:
        await disc_user.move_to(team_voice_channel)
    except Exception:
        pass


async def move_all_team_players_to_lobby(ctx: ApplicationContext):
    """For the end of a game, moves all players that are in team_1 or team_2 back to the lobby."""
    if ctx.guild is None:
        raise NoGuildException
    lobby_voice_channel = ctx.guild.get_channel(LOBBY_CHANNEL_ID)
    team_1_voice_channel = ctx.guild.get_channel(TEAM_1_CHANNEL_ID)
    team_2_voice_channel = ctx.guild.get_channel(TEAM_2_CHANNEL_ID)
    if lobby_voice_channel is None:
        raise CouldNotFindChannelException("Lobby Voice Channel", LOBBY_CHANNEL_ID)
    if team_1_voice_channel is None:
        raise CouldNotFindChannelException("Team 1 Voice Channel", TEAM_1_CHANNEL_ID)
    if team_2_voice_channel is None:
        raise CouldNotFindChannelException("Team 2 Voice Channel", TEAM_2_CHANNEL_ID)
    for member in team_1_voice_channel.members:
        await member.move_to(lobby_voice_channel)
    for member in team_2_voice_channel.members:
        await member.move_to(lobby_voice_channel)


def end_game(ctx: ApplicationContext, winner: str) -> None:
    """
    If a game is currently running, ends the game and moves all players back to the lobby.
    Winner: The team that won the game.
    """
    if ctx.guild is None:
        raise NoGuildException
    assert type(ctx.user) is Member
    if ADMIN_ID in [role.id for role in ctx.user.roles] or ctx.user.guild_permissions.administrator:
        if not CurrentGame().in_progress:
            raise NoGameInProgressException("No game is currently in progress.")
        if winner == "team 1":
            winning_team = CurrentGame().team_1
            losing_team = CurrentGame().team_2
        elif winner == "team 2":
            winning_team = CurrentGame().team_2
            losing_team = CurrentGame().team_1
        else:
            raise Exception("Invalid winner")

        logger.info(f"\nI think the winning team is {winning_team}\n")
        logger.info(f"\nI think the losing team is {losing_team}\n")
        # Update the ratings of the players
        winning_team_ratings = [player.rating for player in winning_team.values()]
        logger.info(f"\nWinning team ratings: {winning_team_ratings}")
        losing_team_ratings = [player.rating for player in losing_team.values()]
        logger.info(f"\nLosing team ratings: {losing_team_ratings}")
        winning_team_ratings, losing_team_ratings = trueskill.rate(
            [winning_team_ratings, losing_team_ratings], ranks=[0, 1]
        )
        logger.info(f"\nUpdated Winning team ratings: {winning_team_ratings}")
        logger.info(f"\nUpdated Losing team ratings: {losing_team_ratings}")

        # Update players' ratings in the tracked player stats, and then re-add them to the queue
        for player in winning_team.values():
            logger.info(f"Updating player {player.user.display_name}...")
            player.report_player_data(win=True)
        for player in losing_team.values():
            logger.info(f"Updating player {player.user.display_name}...")
            player.report_player_data(win=False)

        # Update the saved data to match the data in memory
        logger.info("Running update_player_data()...")
        PlayerData().update_player_data()
        logger.info("Player data updated!")

        # Reset the current game.
        CurrentGame().reset_state()

    else:
        raise NotAdminException("You must be an admin to report the end of a game.")


def cancel_game(ctx: ApplicationContext) -> None:
    """If a game is currently running, ends the game and moves all players back to the lobby without reporting winners."""
    if ctx.guild is None:
        raise NoGuildException
    assert type(ctx.user) is Member
    if ADMIN_ID in [role.id for role in ctx.user.roles] or ctx.user.guild_permissions.administrator:
        if not CurrentGame().in_progress:
            raise NoGameInProgressException("No game is currently in progress.")
        # Move everyone back to the lobby.
        CurrentGame().reset_state()

    else:
        raise NotAdminException("You must be an admin to cancel a game.")
