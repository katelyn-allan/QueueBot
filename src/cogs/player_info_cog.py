import discord
from discord import ApplicationContext
import commands.player_stats as player_stats
from exceptions import *
from typing import List, Dict, Any
from discord.ext import commands
from role_ids import *


class PlayerInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="stats", description="Get your stats")
    async def slash_get_stats(self, ctx: ApplicationContext):
        await ctx.respond(str(player_stats.get_player_stats(ctx)))

    @discord.slash_command(name="setup", description="Get set up with the Queue Bot!")
    async def slash_setup(self, ctx: ApplicationContext):
        # Use a discord.ui.Select menu to allow a user to assign roles
        # to themselves
        main_role_select = discord.ui.Select(
            placeholder="Main Role (Select 1)",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Tank",
                    description="Tank",
                    emoji=TANK_EMOJI,
                    value="Tank",
                ),
                discord.SelectOption(
                    label="Support",
                    description="Support",
                    emoji=SUPPORT_EMOJI,
                    value="Support",
                ),
                discord.SelectOption(
                    label="Assassin",
                    description="Assassin",
                    emoji=ASSASSIN_EMOJI,
                    value="Assassin",
                ),
                discord.SelectOption(
                    label="Offlane",
                    description="Offlane",
                    emoji=OFFLANE_EMOJI,
                    value="Offlane",
                ),
            ],
        )
        secondary_role_select = discord.ui.Select(
            placeholder="Fill Roles (Select as many as you want)",
            min_values=0,
            max_values=4,
            options=[
                discord.SelectOption(
                    label="Tank",
                    description="Tank (Fill)",
                    emoji=TANK_EMOJI,
                    value="Tank",
                ),
                discord.SelectOption(
                    label="Support",
                    description="Support (Fill)",
                    emoji=SUPPORT_EMOJI,
                    value="Support",
                ),
                discord.SelectOption(
                    label="Assassin",
                    description="Assassin (Fill)",
                    emoji=ASSASSIN_EMOJI,
                    value="Assassin",
                ),
                discord.SelectOption(
                    label="Offlane",
                    description="Offlane (Fill)",
                    emoji=OFFLANE_EMOJI,
                    value="Offlane",
                ),
            ],
        )
        row = discord.ActionRow(main_role_select, secondary_role_select)
        await ctx.respond(
            "Select your main role and any secondary roles you feel comfortable filling! Your main role will always be prioritized for matchmaking.",
            components=[row],
        )


def setup(bot: commands.Bot):
    bot.add_cog(PlayerInfoCog(bot))
