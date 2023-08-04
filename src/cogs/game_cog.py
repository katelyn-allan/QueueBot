import discord
from discord import ApplicationContext
import commands.game as game
from exceptions import *
from typing import List, Dict, Any
from discord.ext import commands
from role_ids import *


class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def convert_team_to_string(self, team: Dict[str, game.Player]) -> str:
        return_str = ""
        for role in ["tank", "support", "assassin", "assassin2", "offlane"]:
            return_str += f"<@{team[role].user.id}>\n\n"
        return return_str

    @discord.slash_command(name="start", description="Start a game")
    async def slash_start_game(self, ctx: ApplicationContext):
        try:
            current_game = await game.start_game(ctx)
            map: str = current_game["map"]
            team1: Dict[str, game.Player] = current_game["team1"]
            team2: Dict[str, game.Player] = current_game["team2"]
            fp = current_game["first_pick"]

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
                name=f"Team 1" + (" (First Pick)" if fp == 1 else ""),
                value=self.convert_team_to_string(team1),
                inline=True,
            )
            embed.add_field(
                name="VS.",
                value=f"TANK\n\nSUPPORT\n\nASSASSIN\n\nASSASSIN\n\nOFFLANE",
            )
            embed.add_field(
                name=f"Team 2" + (" (First Pick)" if fp == 2 else ""),
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
    async def slash_end_game(self, ctx: ApplicationContext, winner: int):
        try:
            await game.end_game(ctx, winner)
            embed = discord.Embed(
                title="Game Ended",
                color=discord.Colour.blurple(),
                description=f"Game ended by {ctx.user.mention}! Team {winner} are the winners!",
            )
            await ctx.respond(
                embed=embed,
            )
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
    async def slash_cancel_game(self, ctx: ApplicationContext):
        try:
            await game.cancel_game(ctx)
            embed = discord.Embed(
                title="Game Cancelled",
                color=discord.Colour.blurple(),
                description=f"Game cancelled by {ctx.user.mention}!",
            )
            await ctx.respond(
                embed=embed,
            )
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


def setup(bot: commands.Bot):
    bot.add_cog(GameCog(bot))
