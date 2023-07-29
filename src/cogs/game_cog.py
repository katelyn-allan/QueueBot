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

    @discord.slash_command(name="start", description="Start a game")
    async def slash_start_game(self, ctx: ApplicationContext):
        try:
            await ctx.respond(game.start_game(ctx))
        except NotEnoughPlayersException:
            await ctx.respond("Not enough players to start a game!")
        except GameIsInProgressException:
            await ctx.respond("Game is already in progress!")

    @discord.slash_command(name="test_game_display", description="Test game display")
    async def slash_test_game_display(self, ctx: ApplicationContext):
        banner = "https://static.icy-veins.com/images/heroes/tier-lists/maps/infernal-shrines.jpg"
        embed = discord.Embed(
            title="***Game Started***",
            color=discord.Colour.blurple(),
            description="INFERNAL SHRINES",
        )
        embed.set_author(
            name=f"Started by <@{ctx.author.id}>",
            icon_url=ctx.user.avatar,
        )
        embed.add_field(
            name=f"Team 1 (FP)",
            value=f"<@{ctx.author.id}>\n\n<@{ctx.author.id}>\n\n<@{ctx.author.id}>\n\n<@{ctx.author.id}>\n\n<@{ctx.author.id}>",
            inline=True,
        )
        embed.add_field(
            name="VS.",
            value=f"{TANK_EMOJI}\n\n{SUPPORT_EMOJI}\n\n{ASSASSIN_EMOJI}\n\n{ASSASSIN_EMOJI}\n\n{OFFLANE_EMOJI}",
        )
        embed.add_field(
            name=f"Team 2",
            value=f"<@{ctx.author.id}>\n\n<@{ctx.author.id}>\n\n<@{ctx.author.id}>\n\n<@{ctx.author.id}>\n\n<@{ctx.author.id}>",
            inline=True,
        )
        embed.set_image(url=banner)
        await ctx.respond(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(GameCog(bot))
