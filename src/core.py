import discord
import os
from dotenv import load_dotenv
from discord import ApplicationContext
import commands.queue as queue
import commands.player_stats as player_stats
import commands.game as game
from typing import List, Dict, Any

# import commands.game as game
from role_ids import *
from exceptions import *

# Load environment variables
load_dotenv()
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")

bot = discord.Bot()


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


# # QUEUE COMMANDS
@bot.slash_command(name="join", description="Join the queue for a game")
async def slash_join_queue(ctx: ApplicationContext):
    try:
        user_id, queue_length = queue.join_queue(ctx)
    except AlreadyInQueueException as e:
        await ctx.respond(f"<@{e.user.id}> is already in the queue!")
        return
    if queue_length == 1:
        await ctx.respond(
            f"<@{user_id}> has joined the queue! There is now {queue_length} player in the queue."
        )
    else:
        await ctx.respond(
            f"<@{user_id}> has joined the queue! There are now {queue_length} players in the queue."
        )


def convert_list_to_string(l: List) -> str:
    return_str = ""
    for item in l:
        return_str += f"{item}\n"
    return return_str


@bot.slash_command(name="list", description="List the players in the queue")
async def slash_list_queue(ctx: ApplicationContext):
    queue_info = queue.list_queue(ctx)
    thumbnail = discord.File("images/hotslogo.png", filename="hotslogo.png")
    embed = discord.Embed(
        title="Queue",
        color=discord.Colour.blurple(),
        description=f"Players in Queue: {len(queue.QUEUE)}",
    )
    embed.add_field(
        name="Tanks <:tank:1113243868352233493>",
        value=convert_list_to_string(queue_info.get("Tanks", [])),
        inline=False,
    )
    embed.add_field(
        name="Supports <:healer:1113243864166305922>",
        value=convert_list_to_string(queue_info.get("Supports", [])),
        inline=False,
    )
    embed.add_field(
        name="Assassins <:assassin:1113243855442169897>",
        value=convert_list_to_string(queue_info.get("Assassins", [])),
        inline=False,
    )
    embed.add_field(
        name="Offlanes <:bruiser:1113243858759860326>",
        value=convert_list_to_string(queue_info.get("Offlanes", [])),
        inline=False,
    )
    embed.set_thumbnail(url="attachment://hotslogo.png")
    await ctx.respond(file=thumbnail, embed=embed)


@bot.slash_command(name="leave", description="Leave the queue for a game")
async def slash_leave_queue(ctx: ApplicationContext):
    try:
        user_id, queue_length = queue.leave_queue(ctx)
    except PlayerNotFoundException as e:
        await ctx.respond(f"<@{e.user.id}> is not in the queue!")
        return
    if queue_length == 1:
        await ctx.respond(
            f"<@{user_id}> has left the queue! There is now {queue_length} player in the queue."
        )
    else:
        await ctx.respond(
            f"<@{user_id}> has left the queue! There are now {queue_length} players in the queue."
        )


@bot.slash_command(name="clear", description="Clear the queue")
async def slash_clear_queue(ctx: ApplicationContext):
    if (
        ADMIN_ID in [role.id for role in ctx.user.roles]
        or ctx.user.guild_permissions.administrator
    ):
        queue.clear_queue()
        await ctx.respond("Queue cleared!")
    else:
        await ctx.respond("Only Bot Engineers or Administrators can clear the queue!")


# # GAME COMMANDS
@bot.slash_command(name="start", description="Start a game")
async def slash_start_game(ctx: ApplicationContext):
    try:
        await ctx.respond(game.start_game(ctx))
    except NotEnoughPlayersException:
        await ctx.respond("Not enough players to start a game!")
    except GameIsInProgressException:
        await ctx.respond("Game is already in progress!")


# # PLAYER COMMANDS
@bot.slash_command(name="stats", description="Get your stats")
async def slash_get_stats(ctx: ApplicationContext):
    await ctx.respond(str(player_stats.get_player_stats(ctx)))


if __name__ == "__main__":
    bot.run(AUTH_TOKEN)
