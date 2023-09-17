import discord
from discord import ApplicationContext, option, Forbidden, HTTPException
import commands.game as game
from typing import Self
from discord.ext import commands

from util.exceptions import (
    GameInProgressException,
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

    @discord.slash_command(name="start", description="Start a game")
    async def slash_start_game(self: Self, ctx: ApplicationContext) -> None:
        """Starts a game."""
        await ctx.defer()
        try:
            current_game = await game.start_game(ctx)
            if current_game:
                current_game = game.CurrentGame()
                embed = current_game.create_embed()
                embed.set_author(
                    name=f"Started by {ctx.user.display_name}",
                    icon_url=ctx.user.display_avatar,
                )
                await ctx.respond(embed=embed)
                # Move players after the embed is sent.
                for player in current_game.team_1.values():
                    await game.move_player_from_lobby_to_team_voice(player.user, 1, ctx)
                for player in current_game.team_2.values():
                    await game.move_player_from_lobby_to_team_voice(player.user, 2, ctx)
        except NotEnoughPlayersException:
            await ctx.defer(ephemeral=True)
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="Not enough players to start a game!",
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except GameInProgressException:
            await ctx.defer(ephemeral=True)
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="Game is already in progress!",
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except NotAdminException:
            await ctx.defer(ephemeral=True)
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
        await ctx.defer()
        try:
            game.end_game(ctx, winner)

            embed = discord.Embed(
                title="Game Ended",
                color=discord.Colour.blurple(),
                description=f"Game ended by {ctx.user.mention}! Team {winner} are the winners!",
            )
            await ctx.respond(embed=embed)

            try:
                await game.move_all_team_players_to_lobby(ctx)
            except Forbidden | HTTPException as e:
                logger.error(e)
                pass
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
        await ctx.defer()
        try:
            game.cancel_game(ctx)

            embed = discord.Embed(
                title="Game Cancelled",
                color=discord.Colour.blurple(),
                description=f"Game cancelled by {ctx.user.mention}!",
            )
            await ctx.respond(embed=embed)

            try:
                await game.move_all_team_players_to_lobby(ctx)
            except Forbidden | HTTPException as e:
                logger.error(e)
                pass
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

    @discord.slash_command(name="reroll", description="Reroll the map of the currently running game")
    async def slash_reroll_game(self: Self, ctx: ApplicationContext) -> None:
        """Rerolls the map of a currently running game."""
        await ctx.defer()
        try:
            game.CurrentGame().reroll_map()
            embed = game.CurrentGame().create_embed()
            embed.set_author(
                name=f"Started by {ctx.user.display_name}",
                icon_url=ctx.user.display_avatar,
            )
            await ctx.respond(embed=embed)
        except NoGameInProgressException:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="No game is currently in progress!",
            )
            await ctx.respond(embed=embed, ephemeral=True)


def setup(bot: discord.Bot) -> None:
    """Adds this cog to the bot."""
    bot.add_cog(GameCog(bot))
