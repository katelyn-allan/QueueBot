import discord
import os
from dotenv import load_dotenv
import logging

from commands.queue import populate_queue
from util.env_load import GENERAL_CHANNEL_ID

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
        queue_length = populate_queue(guild)
        try:
            general = guild.get_channel(GENERAL_CHANNEL_ID)
            embed = discord.Embed(
                title="Startup",
                color=discord.Colour.blurple(),
                description=f"I'm awake! Queue is now open and initialized with {queue_length} players.",
            )
            await general.send(embed=embed)
        except discord.errors.NotFound:
            logger.error(f"Could not find channel {GENERAL_CHANNEL_ID} for guild [{guild.id}]:{guild.name}")
            continue


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
    )
    bot.load_extension("cogs.game_cog")
    bot.load_extension("cogs.queue_cog")
    bot.load_extension("cogs.player_info_cog")
    bot.run(AUTH_TOKEN)
