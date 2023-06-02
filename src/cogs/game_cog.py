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


def setup(bot: commands.Bot):
    bot.add_cog(GameCog(bot))
