import discord
from discord import ApplicationContext

from commands.queue import Queue
from typing import Self

from discord.ext import commands

from util.env_load import ADMIN_ID, ASSASSIN_EMOJI, OFFLANE_EMOJI, QUEUED_ID, SUPPORT_EMOJI, TANK_EMOJI
from util.exceptions import AlreadyInQueueException, NoMainRoleException, PlayerNotFoundException


class QueueCog(commands.Cog):
    """Commands for interacting with the Queue."""

    def __init__(self: Self, bot: discord.Bot) -> None:
        """Initialize this cog with the bot."""
        self.bot: discord.Bot = bot

    @discord.slash_command(name="join", description="Join the queue for a game")
    async def slash_join_queue(self: Self, ctx: ApplicationContext) -> None:
        """Joins the queue."""
        try:
            user_id, queue_length = Queue().join_queue(ctx)
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
                description=f"<@{e.user.id}>, you do not have a main role set! Please setup using the `/setup` command and then try again.",  # noqa: E501
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        embed = discord.Embed(
            title="Queue",
            color=discord.Colour.blurple(),
            description=f"<@{user_id}> has joined the queue! There {plural_2} now {queue_length} player{plural} in the queue.",  # noqa: E501
        )
        await ctx.respond(embed=embed)

    @discord.slash_command(name="list", description="List the players in the queue")
    async def slash_list_queue(self: Self, ctx: ApplicationContext) -> None:
        """Lists the queue in a stylized format."""
        queue_info = Queue().as_dict()
        thumbnail = discord.File("images/hotslogo.png", filename="hotslogo.png")
        embed = discord.Embed(
            title="Queue",
            color=discord.Colour.blurple(),
            description=f"Players in Queue: {len(Queue.queue)}",
        )
        embed.add_field(
            name=f"Tanks {TANK_EMOJI}",
            value="\n".join(queue_info.get("Tanks", [])),
            inline=True,
        )
        embed.add_field(
            name=f"Tanks (FILL) {TANK_EMOJI}",
            value="\n".join(queue_info.get("Tanks (Fill)", [])),
            inline=True,
        )
        embed.add_field(name="", value="\n")
        embed.add_field(
            name=f"Supports {SUPPORT_EMOJI}",
            value="\n".join(queue_info.get("Supports", [])),
            inline=True,
        )
        embed.add_field(
            name=f"Supports (FILL) {SUPPORT_EMOJI}",
            value="\n".join(queue_info.get("Supports (Fill)", [])),
            inline=True,
        )
        embed.add_field(name="", value="\n")
        embed.add_field(
            name=f"Assassins {ASSASSIN_EMOJI}",
            value="\n".join(queue_info.get("Assassins", [])),
            inline=True,
        )
        embed.add_field(
            name=f"Assassins (FILL) {ASSASSIN_EMOJI}",
            value="\n".join(queue_info.get("Assassins (Fill)", [])),
            inline=True,
        )
        embed.add_field(name="", value="\n")
        embed.add_field(
            name=f"Offlanes {OFFLANE_EMOJI}",
            value="\n".join(queue_info.get("Offlanes", [])),
            inline=True,
        )
        embed.add_field(
            name=f"Offlanes (FILL) {OFFLANE_EMOJI}",
            value="\n".join(queue_info.get("Offlanes (Fill)", [])),
            inline=True,
        )
        embed.add_field(name="", value="\n")
        embed.set_thumbnail(url="attachment://hotslogo.png")
        await ctx.respond(file=thumbnail, embed=embed)

    @discord.slash_command(name="leave", description="Leave the queue for a game")
    async def slash_leave_queue(self: Self, ctx: ApplicationContext) -> None:
        """Leaves the queue."""
        try:
            user_id, queue_length = Queue().leave_queue(ctx)
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
            description=f"<@{user_id}> has left the queue! There {plural_2} now {queue_length} player{plural} in the queue.",  # noqa: E501
        )
        await ctx.respond(embed=embed)

    @discord.slash_command(name="clear", description="Clear the queue")
    async def slash_clear_queue(self: Self, ctx: ApplicationContext) -> None:
        """Clears the queue. Admin command."""
        if ADMIN_ID in [role.id for role in ctx.user.roles] or ctx.user.guild_permissions.administrator:
            Queue().queue.clear()
            queued_role = ctx.guild.get_role(QUEUED_ID)
            for member in ctx.guild.members:
                if queued_role in member.roles:
                    await member.remove_roles(queued_role)
            embed = discord.Embed(
                title="Queue",
                color=discord.Colour.blurple(),
                description="Queue cleared!",
            )
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="Only Bot Engineers or Administrators can clear the queue!",
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @discord.slash_command(name="remove", description="Remove a player from the queue")
    async def slash_remove_player(self: Self, ctx: ApplicationContext, user: discord.Member) -> None:
        """Removes a player from the queue. Admin command."""
        if ADMIN_ID in [role.id for role in ctx.user.roles] or ctx.user.guild_permissions.administrator:
            try:
                user_id, queue_length = Queue().remove_from_queue(user)
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
                description=f"<@{user_id}> has been removed from the queue! There {plural_2} now {queue_length} player{plural} in the queue.",  # noqa: E501
            )
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title="Error",
                color=discord.Colour.red(),
                description="Only Bot Engineers or Administrators can clear the queue!",
            )
            await ctx.respond(embed=embed, ephemeral=True)


def setup(bot: discord.Bot) -> None:
    """Adds this cog to the bot."""
    bot.add_cog(QueueCog(bot))
