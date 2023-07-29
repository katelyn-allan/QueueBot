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
            return_str += f"{team[role].id}\n\n"
        return return_str

    @discord.slash_command(name="start", description="Start a game")
    async def slash_start_game(self, ctx: ApplicationContext):
        try:
            current_game = game.start_game(ctx)
            map: str = current_game["map"]
            team1: Dict[str, game.Player] = current_game["team1"]
            team2: Dict[str, game.Player] = current_game["team2"]
            fp = current_game["first_pick"]

            for player in team1.values():
                game.move_player_from_lobby_to_team_voice(player, 1, ctx)
            for player in team2.values():
                game.move_player_from_lobby_to_team_voice(player, 2, ctx)

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
            await ctx.respond("Not enough players to start a game!")
        except GameIsInProgressException:
            await ctx.respond("Game is already in progress!")


def setup(bot: commands.Bot):
    bot.add_cog(GameCog(bot))
