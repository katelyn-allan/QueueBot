import discord
import os
from dotenv import load_dotenv
import logging
from util.env_load import *
from util.exceptions import *

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
