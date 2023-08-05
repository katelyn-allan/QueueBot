import discord
from discord import ApplicationContext
import commands.queue as queue
from exceptions import *
from typing import List, Dict, Any
from discord.ext import commands
from role_ids import *


class QueueCog(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot

    @discord.slash_command(name="join", description="Join the queue for a game")
    async def slash_join_queue(self, ctx: ApplicationContext):
        try:
            user_id, queue_length = queue.join_queue(ctx)
            queued_role = ctx.guild.get_role(QUEUED_ID)
            await ctx.user.add_roles(queued_role)
            plural = "s" if queue_length != 1 else ""
            plural_2 = "is" if queue_length == 1 else "are"
        except AlreadyInQueueException as e:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description=f"<@{e.user.id}> is already in the queue!",
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        except NoMainRoleException as e:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description=f"<@{e.user.id}>, you do not have a main role set! Please setup using the `/setup` command and then try again.",
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        embed = discord.Embed(
            title="Queue",
            color=discord.Colour.blurple(),
            description=f"<@{user_id}> has joined the queue! There {plural_2} now {queue_length} player{plural} in the queue.",
        )
        await ctx.respond(embed=embed)
        await queue.update_queue_channel(ctx, queue_length)

    def convert_list_to_string(self, l: List[Any]) -> str:
        return_str = ""
        for item in l:
            return_str += f"{item}\n"
        return return_str

    @discord.slash_command(name="list", description="List the players in the queue")
    async def slash_list_queue(self, ctx: ApplicationContext):
        queue_info = queue.get_queue_data(ctx)
        thumbnail = discord.File("images/hotslogo.png", filename="hotslogo.png")
        embed = discord.Embed(
            title="Queue",
            color=discord.Colour.blurple(),
            description=f"Players in Queue: {len(queue.QUEUE)}",
        )
        embed.add_field(
            name=f"Tanks {TANK_EMOJI}",
            value=self.convert_list_to_string(queue_info.get("Tanks", [])),
            inline=True,
        )
        embed.add_field(
            name=f"Tanks (FILL) {TANK_EMOJI}",
            value=self.convert_list_to_string(queue_info.get("Tanks (Fill)", [])),
            inline=True,
        )
        embed.add_field(name="", value="\n")
        embed.add_field(
            name=f"Supports {SUPPORT_EMOJI}",
            value=self.convert_list_to_string(queue_info.get("Supports", [])),
            inline=True,
        )
        embed.add_field(
            name=f"Supports (FILL) {SUPPORT_EMOJI}",
            value=self.convert_list_to_string(queue_info.get("Supports (Fill)", [])),
            inline=True,
        )
        embed.add_field(name="", value="\n")
        embed.add_field(
            name=f"Assassins {ASSASSIN_EMOJI}",
            value=self.convert_list_to_string(queue_info.get("Assassins", [])),
            inline=True,
        )
        embed.add_field(
            name=f"Assassins (FILL) {ASSASSIN_EMOJI}",
            value=self.convert_list_to_string(queue_info.get("Assassins (Fill)", [])),
            inline=True,
        )
        embed.add_field(name="", value="\n")
        embed.add_field(
            name=f"Offlanes {OFFLANE_EMOJI}",
            value=self.convert_list_to_string(queue_info.get("Offlanes", [])),
            inline=True,
        )
        embed.add_field(
            name=f"Offlanes (FILL) {OFFLANE_EMOJI}",
            value=self.convert_list_to_string(queue_info.get("Offlanes (Fill)", [])),
            inline=True,
        )
        embed.add_field(name="", value="\n")
        embed.set_thumbnail(url="attachment://hotslogo.png")
        await ctx.respond(file=thumbnail, embed=embed)

    @discord.slash_command(name="leave", description="Leave the queue for a game")
    async def slash_leave_queue(self, ctx: ApplicationContext):
        try:
            user_id, queue_length = queue.leave_queue(ctx)
            queued_role = ctx.guild.get_role(QUEUED_ID)
            await ctx.user.remove_roles(queued_role)
            plural = "s" if queue_length != 1 else ""
            plural_2 = "is" if queue_length == 1 else "are"
        except PlayerNotFoundException as e:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description=f"<@{e.user.id}> is not in the queue!",
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        embed = discord.Embed(
            title="Queue",
            color=discord.Colour.blurple(),
            description=f"<@{user_id}> has left the queue! There {plural_2} now {queue_length} player{plural} in the queue.",
        )
        await ctx.respond(embed=embed)
        await queue.update_queue_channel(ctx, queue_length)

    @discord.slash_command(name="clear", description="Clear the queue")
    async def slash_clear_queue(self, ctx: ApplicationContext):
        if (
            ADMIN_ID in [role.id for role in ctx.user.roles]
            or ctx.user.guild_permissions.administrator
        ):
            await queue.clear_queue(ctx)
            queued_role = ctx.guild.get_role(QUEUED_ID)
            for member in ctx.guild.members:
                if queued_role in member.roles:
                    await member.remove_roles(queued_role)
            embed = discord.Embed(
                title="Queue",
                color=discord.Colour.blurple(),
                description=f"Queue cleared!",
            )
            await ctx.respond(embed=embed)
            await queue.update_queue_channel(ctx, 0)
        else:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="Only Bot Engineers or Administrators can clear the queue!",
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @discord.slash_command(name="remove", description="Remove a player from the queue")
    async def slash_remove_player(self, ctx: ApplicationContext, user: discord.Member):
        if (
            ADMIN_ID in [role.id for role in ctx.user.roles]
            or ctx.user.guild_permissions.administrator
        ):
            try:
                user_id, queue_length = queue.remove_from_queue(ctx, user)
                # Remove the queued role from the user
                queued_role = ctx.guild.get_role(QUEUED_ID)
                await user.remove_roles(queued_role)
                plural = "s" if queue_length != 1 else ""
                plural_2 = "is" if queue_length == 1 else "are"
            except PlayerNotFoundException as e:
                embed = discord.Embed(
                    title="Error",
                    color=discord.Colour.red(),
                    description=f"<@{e.user.id}> is not in the queue or could not be found!",
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
            embed = discord.Embed(
                title="Queue",
                color=discord.Colour.blurple(),
                description=f"<@{user_id}> has been removed from the queue! There {plural_2} now {queue_length} player{plural} in the queue.",
            )
            await ctx.respond(embed=embed)
            await queue.update_queue_channel(ctx, queue_length)
        else:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="Only Bot Engineers or Administrators can clear the queue!",
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @discord.slash_command(name="initialize", description="Initialize the bot")
    async def slash_initialize(self, ctx: ApplicationContext):
        if (
            ADMIN_ID in [role.id for role in ctx.user.roles]
            or ctx.user.guild_permissions.administrator
        ):
            queue_len = queue.populate_queue(ctx)
            await queue.update_queue_channel(ctx, queue_len)
            embed = discord.Embed(
                title="Queue",
                color=discord.Colour.blurple(),
                description=f"Bot initialized and queue populated.",
            )
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="Only Bot Engineers or Administrators can initialize the bot!",
            )
            await ctx.respond(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(QueueCog(bot))
