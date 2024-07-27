from enum import Enum
from sqlalchemy.orm import scoped_session
import trueskill
from discord import ApplicationContext, Member, Forbidden, HTTPException
from commands.queue import Queue
from database.models.player_data import PlayerData
from database.db import DBGlobalSession
from typing import List, Dict, Optional, Self, Type
import numpy as np
import itertools
from scipy.optimize import linear_sum_assignment
import random
from util.env_load import ADMIN_ID, LOBBY_CHANNEL_ID, TEAM_1_CHANNEL_ID, TEAM_2_CHANNEL_ID

from util.exceptions import (
    ChannelNotFoundException,
    GameInProgressException,
    NoGameInProgressException,
    NoGuildException,
    NoValidGameException,
    NotAdminException,
)
import logging
import discord

logger = logging.getLogger(__name__)


class RoleEnum(Enum):
    """Enum class to store roles."""

    TANK = "tank"
    SUPPORT = "support"
    ASSASSIN = "assassin"
    ASSASSIN2 = "assassin2"
    OFFLANE = "offlane"

    def __eq__(self: Self, other: str) -> bool:
        """Override equality to allow for comparison with strings."""
        if isinstance(other, RoleEnum):
            return self.value == other.value
        elif isinstance(other, str):
            return self.value == other
        return NotImplemented

    def __repr__(self: Self) -> str:
        """Override repr to return the role string."""
        return self.value

    def __str__(self: Self) -> str:
        """Override str to return the role string."""
        return self.value

    def __hash__(self: Self) -> int:
        """Override hash to return the hash of the role string."""
        return hash(self.value)


def convert_int_to_role(role_int: int) -> RoleEnum:
    """Helper function which turns a cost matrix indicy into a role string."""
    if role_int == 0 or role_int == 1:
        return RoleEnum.TANK
    elif role_int == 2 or role_int == 3:
        return RoleEnum.SUPPORT
    elif role_int == 4 or role_int == 5 or role_int == 6 or role_int == 7:
        return RoleEnum.ASSASSIN
    elif role_int == 8 or role_int == 9:
        return RoleEnum.OFFLANE
    else:
        raise ValueError("Invalid `role_int`. Must be a number within 0-9.")


class Player:
    """Class to store a player's role for use in the game."""

    def __init__(self: Self, user: Member, role: RoleEnum) -> None:
        """Init that takes in a user and role argument to create a Player object.

        Because the default User or Member class does not allow for role assignment, this class acts
        as a superclass of that more or less that allows for the role to be stored, along with the respective rating.
        """
        self.user = user
        self.role = role

    def calculate_trueskill(self: Self, data: PlayerData) -> trueskill.Rating:
        """Calculates the trueskill rating of a player based on their role."""
        if self.role == RoleEnum.ASSASSIN2:
            lookup_role = RoleEnum.ASSASSIN
        else:
            lookup_role = self.role
        mu = getattr(data, f"{lookup_role}_mu")
        sigma = getattr(data, f"{lookup_role}_sigma")
        return trueskill.Rating(mu, sigma)


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

    def reroll_map(self: Self) -> None:
        """Reroll the map for the current game."""
        if self.in_progress:
            valid_maps_copy = self.valid_maps.copy()
            valid_maps_copy.remove(self.map)
            self.map = random.choice(valid_maps_copy)
        else:
            raise NoGameInProgressException("No game is currently in progress.")

    def convert_team_to_string(self: Self, team: Dict[str, Player]) -> str:
        """Helper function to convert a provided team dictionary to a string representation.

        TODO: Convert team to a class structure and add a __str__ method for this.
        """
        return_str = ""
        for role in ["tank", "support", "assassin", "assassin2", "offlane"]:
            return_str += f"<@{team[role].user.id}>\n\n"
        return return_str

    def create_embed(self: Self) -> discord.Embed:
        """Creates a discord embed object representing the game."""
        banner = f"https://static.icy-veins.com/images/heroes/tier-lists/maps/{self.map.replace(' ', '-').lower()}.jpg"
        embed = discord.Embed(
            title="**Game Started**",
            color=discord.Colour.blurple(),
            description=self.map,
        )
        embed.add_field(
            name="Team 1" + (" (First Pick)" if self.first_pick == 1 else ""),
            value=self.convert_team_to_string(self.team_1),
            inline=True,
        )
        embed.add_field(
            name="VS.",
            value="TANK\n\nSUPPORT\n\nASSASSIN\n\nASSASSIN\n\nOFFLANE",
        )
        embed.add_field(
            name="Team 2" + (" (First Pick)" if self.first_pick == 2 else ""),
            value=self.convert_team_to_string(self.team_2),
            inline=True,
        )
        embed.set_image(url=banner)
        return embed


def find_valid_game_for_permutation(perm: List[Member]) -> Optional[Dict[str, List[Player]]]:
    """For a permutation of 10 players, find a valid game, if one exists.

    Uses the Hungarian Algorithm to resolve role priority.

    A valid game has: 2 tanks, 2 supports, 4 assassins, and 2 offlanes.
    Players are priotized onto their primary role.

    For each player in the queue, create a numpy matrix,
    where the rows are the players, and the columns are
    the roles (Tank, Healer, Assassin, Offlane).
    The cost of each player to be assigned to a role is 0 if they have the role,
    1 if they are a fill, and 2 if they do not have any roles.
    """
    matrix = np.full((len(perm), 10), 2)
    for i, player in enumerate(perm):
        for role in player.roles:
            match role.name:
                case "Tank":
                    matrix[i][0] = 0
                    matrix[i][1] = 0
                case "Tank (Fill)":
                    matrix[i][0] = 1
                    matrix[i][1] = 1
                case "Support":
                    matrix[i][2] = 0
                    matrix[i][3] = 0
                case "Support (Fill)":
                    matrix[i][2] = 1
                    matrix[i][3] = 1
                case "Assassin":
                    matrix[i][4] = 0
                    matrix[i][5] = 0
                    matrix[i][6] = 0
                    matrix[i][7] = 0
                case "Assassin (Fill)":
                    matrix[i][4] = 1
                    matrix[i][5] = 1
                    matrix[i][6] = 1
                    matrix[i][7] = 1
                case "Offlane":
                    matrix[i][8] = 0
                    matrix[i][9] = 0
                case "Offlane (Fill)":
                    matrix[i][8] = 1
                    matrix[i][9] = 1
    # Find the optimal matching using the Hungarian Algorithm
    # https://docs.scipy.org/doc/scipy-0.18.1/reference/generated/scipy.optimize.linear_sum_assignment.html
    row_ind, col_ind = linear_sum_assignment(matrix)
    # Check if this is a valid set, if not, continue to the next 10 perm.
    if any(matrix[row_ind, col_ind] == 2):
        return
    game_dict = {RoleEnum.TANK: [], RoleEnum.SUPPORT: [], RoleEnum.ASSASSIN: [], RoleEnum.OFFLANE: []}
    for i, player in enumerate(perm):
        role = convert_int_to_role(col_ind[i])
        game_dict[role].append(Player(player, role))
    return game_dict


def find_valid_games() -> List[Dict[str, List[Player]]]:
    """Finds all valid games of 10 players from the queue."""
    players_in_queue: List[Member] = Queue().queue.copy()

    # Ensure all players are in the db
    db_session: scoped_session = DBGlobalSession().new_session()
    for player in players_in_queue:
        player_data = db_session.query(PlayerData).filter(PlayerData.user_id == player.id).first()
        if player_data is None:
            # Create a database entry for this player
            logger.warn(f"Player {player.display_name} not found in database, creating entry...")
            player_data = PlayerData(user_id=player.id)
            db_session.add(player_data)
    db_session.commit()
    db_session.close()

    player_set = set(players_in_queue)
    combinations_of_players: List[List[Member]] = [list(comb) for comb in itertools.combinations(player_set, 10)]
    valid_games = []

    for perm in combinations_of_players:
        valid_game = find_valid_game_for_permutation(perm)
        if valid_game is not None:
            valid_games.append(valid_game)

    return valid_games


def get_team_combinations(players: Dict[str, List[Player]]) -> List[List[List[Player]]]:
    """Finds every combination of players by role and returns a list of unique two team combinations."""
    combinations = []
    for tank in players[RoleEnum.TANK]:
        for support in players[RoleEnum.SUPPORT]:
            for assassin in itertools.combinations(players[RoleEnum.ASSASSIN], 2):
                for offlane in players[RoleEnum.OFFLANE]:
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


def build_trueskill_object_for_list_of_players(
    players: List[Player], db_session: scoped_session = None
) -> Dict[int, trueskill.Rating]:
    """Builds a list of trueskill objects for a list of players."""
    created_session = False
    if db_session is None:
        db_session = DBGlobalSession().new_session()
        created_session = True

    # Collect the user ids
    player_ids = [player.user.id for player in players]
    playerdata_objs = db_session.query(PlayerData).filter(PlayerData.user_id.in_(player_ids)).all()
    playerdata_objs = {player.user_id: player for player in playerdata_objs}

    ratings = {}

    try:
        assert len(playerdata_objs) == len(players)
        ratings = {player.user.id: player.calculate_trueskill(playerdata_objs[player.user.id]) for player in players}

    except AssertionError:
        logger.error("Could not find player data for all players in the game.")
        raise

    finally:
        if created_session:
            db_session.close()

    return ratings


def find_quality_of_teams(team1: List[Player], team2: List[Player], db_session: scoped_session = None) -> float:
    """Finds the quality of two teams."""
    created_session = False
    if db_session is None:
        db_session = DBGlobalSession().new_session()
        created_session = True

    try:
        team1_ratings = build_trueskill_object_for_list_of_players(team1, db_session)
        team2_ratings = build_trueskill_object_for_list_of_players(team2, db_session)
    finally:
        if created_session:
            db_session.close()

    # Calculate the match quality
    return trueskill.quality([team1_ratings.values(), team2_ratings.values()])


def find_best_game(valid_games: List[Dict[str, List[Player]]]) -> Dict[str, Dict[str, Player] | str]:
    """Takes in a set of valid games, broken down by role, and returns the best game by trueskill rating calculation."""
    best_game = None
    best_quality = 10000

    for game in valid_games:
        # Find every permutation of team comp,
        # in which a valid team has 5 players:
        # One tank, One Support, Two Assassins, and One Offlane.
        team_combos: List[List[List[Player]]] = get_team_combinations(game)
        logger.info(f"Found {len(team_combos)} configurations of players for this game group")
        # TODO: Should we instead compare match quality within team_combos and then take a random game?
        for combo in team_combos:
            team1 = combo[0]
            team2 = combo[1]
            match_quality = find_quality_of_teams(team1, team2)
            # Check if match_quality is closer to 0.5 than the current best match_quality.
            if abs(0.5 - match_quality) < abs(0.5 - best_quality):
                best_game = combo
                best_quality = match_quality

    if best_game is None or valid_games == []:
        raise NoValidGameException("No valid game was found.")

    team1 = {}
    team2 = {}
    for player in best_game[0]:
        if player.role == RoleEnum.ASSASSIN and RoleEnum.ASSASSIN in team1:
            team1[RoleEnum.ASSASSIN2] = player
        else:
            team1[player.role] = player
    for player in best_game[1]:
        if player.role == RoleEnum.ASSASSIN and RoleEnum.ASSASSIN in team2:
            team2[RoleEnum.ASSASSIN2] = player
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
        return True
    else:
        raise NotAdminException("You must be an admin to start a game.")


async def move_player_from_lobby_to_team_voice(disc_user: Member, team_number: int, ctx: ApplicationContext) -> None:
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
        raise ValueError("Invalid `team_number`. Must be either 1 or 2.")
    if team_voice_channel is None:
        raise ChannelNotFoundException(f"Team {team_number} Voice Channel", channel_id)
    try:
        await disc_user.move_to(team_voice_channel)
    except Forbidden | HTTPException as e:
        logger.error(e)
        pass


async def move_all_team_players_to_lobby(ctx: ApplicationContext) -> None:
    """For the end of a game, moves all players that are in team_1 or team_2 back to the lobby."""
    if ctx.guild is None:
        raise NoGuildException
    lobby_voice_channel = ctx.guild.get_channel(LOBBY_CHANNEL_ID)
    team_1_voice_channel = ctx.guild.get_channel(TEAM_1_CHANNEL_ID)
    team_2_voice_channel = ctx.guild.get_channel(TEAM_2_CHANNEL_ID)
    if lobby_voice_channel is None:
        raise ChannelNotFoundException("Lobby Voice Channel", LOBBY_CHANNEL_ID)
    if team_1_voice_channel is None:
        raise ChannelNotFoundException("Team 1 Voice Channel", TEAM_1_CHANNEL_ID)
    if team_2_voice_channel is None:
        raise ChannelNotFoundException("Team 2 Voice Channel", TEAM_2_CHANNEL_ID)
    for member in team_1_voice_channel.members:
        await member.move_to(lobby_voice_channel)
    for member in team_2_voice_channel.members:
        await member.move_to(lobby_voice_channel)


def update_player_data_for_team(
    ratings: Dict[int, trueskill.Rating], players: Dict[int, Player], win: bool, db_session: scoped_session
) -> None:
    """Updates the DB record for players on a team to match the new trueskill rating."""
    created_session = False
    if db_session is None:
        db_session = DBGlobalSession().new_session()
        created_session = True

    try:
        for player_id in ratings:
            player: PlayerData = db_session.query(PlayerData).filter(PlayerData.user_id == player_id).first()
            if players[player_id].role == RoleEnum.ASSASSIN2:
                players[player_id].role = RoleEnum.ASSASSIN
            setattr(
                player,
                f"{players[player_id].role}_mu",
                ratings[player_id].mu,
            )
            setattr(
                player,
                f"{players[player_id].role}_sigma",
                ratings[player_id].sigma,
            )
            setattr(
                player,
                f"{players[player_id].role}_games_played",
                getattr(player, f"{players[player_id].role}_games_played") + 1,
            )
            if win:
                setattr(
                    player,
                    f"{players[player_id].role}_games_won",
                    getattr(player, f"{players[player_id].role}_games_won") + 1,
                )

        db_session.flush()

    finally:
        if created_session:
            db_session.commit()
            db_session.close()


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
            raise ValueError("Invalid `winner`. Must be either `team 1` or `team 2`.")

        # Setting up session
        db_session: scoped_session = DBGlobalSession().new_session()

        try:
            logger.info(f"\nI think the winning team is {winning_team}\n")
            logger.info(f"\nI think the losing team is {losing_team}\n")
            # Update the ratings of the players
            winning_team_ratings = build_trueskill_object_for_list_of_players(list(winning_team.values()))
            logger.info(f"\nWinning team ratings: {winning_team_ratings}")
            losing_team_ratings = build_trueskill_object_for_list_of_players(list(losing_team.values()))
            logger.info(f"\nLosing team ratings: {losing_team_ratings}")
            winning_team_ratings, losing_team_ratings = trueskill.rate(
                [winning_team_ratings, losing_team_ratings], ranks=[0, 1]
            )
            logger.info(f"\nUpdated Winning team ratings: {winning_team_ratings}")
            logger.info(f"\nUpdated Losing team ratings: {losing_team_ratings}")

            # Reorganize winning and losing teams into propper structures
            winning_team_players = {player.user.id: player for player in winning_team.values()}
            losing_team_players = {player.user.id: player for player in losing_team.values()}

            # Update players' ratings in the tracked player stats, and then re-add them to the queue
            logger.info("\nUpdating database entries...")
            update_player_data_for_team(winning_team_ratings, winning_team_players, True, db_session)
            update_player_data_for_team(losing_team_ratings, losing_team_players, False, db_session)
            db_session.commit()

            logger.info("\nDatabase updated :)")

            # Reset the current game.
            CurrentGame().reset_state()

        finally:
            db_session.close()

    else:
        raise NotAdminException("You must be an admin to report the end of a game.")


def cancel_game(ctx: ApplicationContext) -> None:
    """Cancels a started game.

    If a game is currently running, ends the game and moves all players
    back to the lobby without reporting winners.
    """
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
