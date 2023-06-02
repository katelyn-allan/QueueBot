import discord
from discord import ApplicationContext
import commands.queue as queue
from exceptions import *
from typing import List, Dict, Any
from discord.ext import commands
from role_ids import *


class QueueCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="join", description="Join the queue for a game")
    async def slash_join_queue(self, ctx: ApplicationContext):
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

    def convert_list_to_string(self, l: List[Any]) -> str:
        return_str = ""
        for item in l:
            return_str += f"{item}\n"
        return return_str

    @discord.slash_command(name="list", description="List the players in the queue")
    async def slash_list_queue(self, ctx: ApplicationContext):
        queue_info = queue.list_queue(ctx)
        thumbnail = discord.File("images/hotslogo.png", filename="hotslogo.png")
        embed = discord.Embed(
            title="Queue",
            color=discord.Colour.blurple(),
            description=f"Players in Queue: {len(queue.QUEUE)}",
        )
        embed.add_field(
            name=f"Tanks {TANK_EMOJI}",
            value=self.convert_list_to_string(queue_info.get("Tanks", [])),
            inline=False,
        )
        embed.add_field(
            name=f"Supports {SUPPORT_EMOJI}",
            value=self.convert_list_to_string(queue_info.get("Supports", [])),
            inline=False,
        )
        embed.add_field(
            name=f"Assassins {ASSASSIN_EMOJI}",
            value=self.convert_list_to_string(queue_info.get("Assassins", [])),
            inline=False,
        )
        embed.add_field(
            name=f"Offlanes {OFFLANE_EMOJI}",
            value=self.convert_list_to_string(queue_info.get("Offlanes", [])),
            inline=False,
        )
        embed.set_thumbnail(url="attachment://hotslogo.png")
        await ctx.respond(file=thumbnail, embed=embed)

    @discord.slash_command(name="leave", description="Leave the queue for a game")
    async def slash_leave_queue(self, ctx: ApplicationContext):
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

    @discord.slash_command(name="clear", description="Clear the queue")
    async def slash_clear_queue(self, ctx: ApplicationContext):
        if (
            ADMIN_ID in [role.id for role in ctx.user.roles]
            or ctx.user.guild_permissions.administrator
        ):
            queue.clear_queue()
            await ctx.respond("Queue cleared!")
        else:
            await ctx.respond(
                "Only Bot Engineers or Administrators can clear the queue!"
            )


def setup(bot: commands.Bot):
    bot.add_cog(QueueCog(bot))
