import discord
from discord import (  # pylint: disable = no-name-in-module
    ApplicationContext,
    option,
    slash_command,
)
from discord.ext import commands

import commands.game as game
from exceptions import (
    ChannelNotFoundException,
    GameInProgressException,
    NoGameInProgressException,
    NoGuildException,
    NotAdminException,
    NotEnoughPlayersException,
)


class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot

    def convert_team_to_string(self, team: dict[str, game.Player]) -> str:
        return_str = ""
        for role in ["tank", "support", "assassin", "assassin2", "offlane"]:
            return_str += f"<@{team[role].user.id}>\n\n"
        return return_str

    @slash_command(name="start", description="Start a game")
    async def slash_start_game(self, ctx: ApplicationContext):
        try:
            current_game = await game.start_game(ctx)
            if current_game:
                current_game = game.CurrentGame()
                print(current_game)
                current_map: str = current_game.map
                team1: dict[str, game.Player] = current_game.team_1
                team2: dict[str, game.Player] = current_game.team_2
                first_pick = current_game.first_pick

            banner = f"https://static.icy-veins.com/images/heroes/tier-lists/maps/{current_map.replace(' ', '-').lower()}.jpg"
            embed = discord.Embed(
                title="**Game Started**",
                color=discord.Colour.blurple(),
                description=current_map,
            )
            embed.set_author(
                name=f"Started by {ctx.user.display_name}",
                icon_url=ctx.user.display_avatar,
            )
            embed.add_field(
                name="Team 1" + (" (First Pick)" if first_pick == 1 else ""),
                value=self.convert_team_to_string(team1),
                inline=True,
            )
            embed.add_field(
                name="VS.",
                value="TANK\n\nSUPPORT\n\nASSASSIN\n\nASSASSIN\n\nOFFLANE",
            )
            embed.add_field(
                name="Team 2" + (" (First Pick)" if first_pick == 2 else ""),
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
        except GameInProgressException:
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

    @slash_command(name="end", description="End a currently running game")
    @option(
        "winner",
        str,
        description="The team that won the game",
        choices=["team 1", "team 2"],
    )
    async def slash_end_game(self, ctx: ApplicationContext, winner: str):
        try:
            game.end_game(ctx, winner)

            # Move everyone back to the lobby.
            try:
                await game.move_all_team_players_to_lobby(ctx)
            except (NoGuildException, ChannelNotFoundException):
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

    @slash_command(name="cancel", description="Cancel a currently running game")
    async def slash_cancel_game(self, ctx: ApplicationContext):
        try:
            game.cancel_game(ctx)
            try:
                await game.move_all_team_players_to_lobby(ctx)
            except (NoGuildException, ChannelNotFoundException):
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


def setup(bot: commands.Bot):
    bot.add_cog(GameCog(bot))
