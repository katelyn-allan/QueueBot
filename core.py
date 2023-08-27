import discord
import os
from dotenv import load_dotenv
import logging
import commands.queue as queue

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")

bot = discord.Bot(intents=discord.Intents.all())


@bot.event
async def on_ready() -> None:
    """
    Function that runs when the bot is connecting to Discord.

    Repopulates queue and updates the according channel.
    """
    logger.info(f"{bot.user} has connected to Discord!")
    for guild in bot.guilds:
        queue.populate_queue(guild)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
    )
    bot.load_extension("cogs.game_cog")
    bot.load_extension("cogs.queue_cog")
    bot.load_extension("cogs.player_info_cog")
    bot.run(AUTH_TOKEN)
