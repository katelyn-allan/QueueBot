import discord
from discord import ApplicationContext, option
import commands.game as game
from typing import Dict, Self
from discord.ext import commands

from util.exceptions import (
    GameIsInProgressException,
    NoGameInProgressException,
    NotAdminException,
    NotEnoughPlayersException,
)

import logging

logger = logging.getLogger(__name__)


class GameCog(commands.Cog):
    """Cog to track commands related to running games."""

    def __init__(self: Self, bot: discord.Bot) -> None:
        """Initialize this cog with the bot."""
        self.bot: discord.Bot = bot

    def convert_team_to_string(self: Self, team: Dict[str, game.Player]) -> str:
        """Helper function to convert a provided team dictionary to a string representation.

        TODO: Convert team to a class structure and add a __str__ method for this.
        """
        return_str = ""
        for role in ["tank", "support", "assassin", "assassin2", "offlane"]:
            return_str += f"<@{team[role].user.id}>\n\n"
        return return_str

    @discord.slash_command(name="start", description="Start a game")
    async def slash_start_game(self: Self, ctx: ApplicationContext) -> None:
        """Starts a game."""
        try:
            current_game = await game.start_game(ctx)
            if current_game:
                current_game = game.CurrentGame()
                map: str = current_game.map
                team1: Dict[str, game.Player] = current_game.team_1
                team2: Dict[str, game.Player] = current_game.team_2
                fp = current_game.first_pick

            banner = f"https://static.icy-veins.com/images/heroes/tier-lists/maps/{map.replace(' ', '-').lower()}.jpg"
            embed = discord.Embed(
                title="**Game Started**",
                color=discord.Colour.blurple(),
                description=map,
            )
            embed.set_author(
                name=f"Started by {ctx.user.display_name}",
                icon_url=ctx.user.display_avatar,
            )
            embed.add_field(
                name="Team 1" + (" (First Pick)" if fp == 1 else ""),
                value=self.convert_team_to_string(team1),
                inline=True,
            )
            embed.add_field(
                name="VS.",
                value="TANK\n\nSUPPORT\n\nASSASSIN\n\nASSASSIN\n\nOFFLANE",
            )
            embed.add_field(
                name="Team 2" + (" (First Pick)" if fp == 2 else ""),
                value=self.convert_team_to_string(team2),
                inline=True,
            )
            embed.set_image(url=banner)
            await ctx.respond(embed=embed)
        except NotEnoughPlayersException:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="Not enough players to start a game!",
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except GameIsInProgressException:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="Game is already in progress!",
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except NotAdminException:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="Only admins can start a game.",
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @discord.slash_command(name="end", description="End a currently running game")
    @option(
        "winner",
        str,
        description="The team that won the game",
        choices=["team 1", "team 2"],
    )
    async def slash_end_game(self: Self, ctx: ApplicationContext, winner: str) -> None:
        """Ends a game, reporting a winner."""
        try:
            game.end_game(ctx, winner)

            # Move everyone back to the lobby.
            try:
                await game.move_all_team_players_to_lobby(ctx)
            except Exception:  # TODO: Make non-generic
                pass
            embed = discord.Embed(
                title="Game Ended",
                color=discord.Colour.blurple(),
                description=f"Game ended by {ctx.user.mention}! Team {winner} are the winners!",
            )
            await ctx.respond(embed=embed)
        except NoGameInProgressException:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="No game is currently in progress!",
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except NotAdminException:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="Only admins can report game results.",
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @discord.slash_command(name="cancel", description="Cancel a currently running game")
    async def slash_cancel_game(self: Self, ctx: ApplicationContext) -> None:
        """Cancels a started game with no winner reported."""
        try:
            game.cancel_game(ctx)
            try:
                await game.move_all_team_players_to_lobby(ctx)
            except Exception as e:  # TODO: Make non-generic
                logger.error(e)
                pass
            embed = discord.Embed(
                title="Game Cancelled",
                color=discord.Colour.blurple(),
                description=f"Game cancelled by {ctx.user.mention}!",
            )
            await ctx.respond(embed=embed)
        except NoGameInProgressException:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="No game is currently in progress!",
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except NotAdminException:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="Only admins can cancel a game.",
            )
            await ctx.respond(embed=embed, ephemeral=True)


def setup(bot: discord.Bot) -> None:
    """Adds this cog to the bot."""
    bot.add_cog(GameCog(bot))
