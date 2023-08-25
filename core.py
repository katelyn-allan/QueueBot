import sys

sys.path.append("src")
import discord
import os
from dotenv import load_dotenv
from discord import ApplicationContext
import commands.queue as queue
import commands.player_stats as player_stats
import commands.game as game
from typing import List, Dict, Any
import logging

# import commands.game as game
from env_load import *
from exceptions import *

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")

bot = discord.Bot(intents=discord.Intents.all())


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


if __name__ == "__main__":
    bot.load_extension("cogs.game_cog")
    bot.load_extension("cogs.queue_cog")
    bot.load_extension("cogs.player_info_cog")
    bot.run(AUTH_TOKEN)
