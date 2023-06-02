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
        await ctx.respond(
            "Select your main and secondary roles. Your main role will always be prioritized for match-making when possible.",
            view=RoleSelectView(),
        )


class RoleSelectView(discord.ui.View):
    @discord.ui.select(
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
    async def main_role_callback(
        self, select: discord.SelectMenu, interaction: discord.Interaction
    ):
        # Disable this menu so the user cannot submit multiple responses.
        select.disabled = True

        # Remove any other role the user has
        for other_role in interaction.user.roles:
            if other_role.name in ["Tank", "Support", "Assassin", "Offlane"]:
                await interaction.user.remove_roles(other_role)

        # Add the role the user selected.
        role_string = select.values[0]
        role = discord.utils.get(interaction.guild.roles, name=role_string)
        await interaction.user.add_roles(role)

        # Report back on our success!
        await interaction.response.edit_message(
            content=f"Added {role_string} role to {interaction.user.mention}",
            view=self,
        )

    @discord.ui.select(
        placeholder="Fill Roles (Select as many as you want)",
        min_values=0,
        max_values=4,
        options=[
            discord.SelectOption(
                label="Tank (Fill)",
                description="Tank (Fill)",
                emoji=TANK_EMOJI,
                value="Tank (Fill)",
            ),
            discord.SelectOption(
                label="Support (Fill)",
                description="Support (Fill)",
                emoji=SUPPORT_EMOJI,
                value="Support (Fill)",
            ),
            discord.SelectOption(
                label="Assassin (Fill)",
                description="Assassin (Fill)",
                emoji=ASSASSIN_EMOJI,
                value="Assassin (Fill)",
            ),
            discord.SelectOption(
                label="Offlane (Fill)",
                description="Offlane (Fill)",
                emoji=OFFLANE_EMOJI,
                value="Offlane (Fill)",
            ),
        ],
    )
    async def secondary_role_callback(
        self, select: discord.SelectMenu, interaction: discord.Interaction
    ):
        # Disable this menu so the user cannot submit multiple responses.
        select.disabled = True

        # Remove any other role the user has
        for other_role in interaction.user.roles:
            if other_role.name in [
                "Tank (Fill)",
                "Support (Fill)",
                "Assassin (Fill)",
                "Offlane (Fill)",
            ]:
                await interaction.user.remove_roles(other_role)

        # Add the roles the user selected.
        role_strings: List[str] = select.values
        roles: List[discord.Role] = [
            discord.utils.get(interaction.guild.roles, name=role_string)
            for role_string in role_strings
        ]
        for role in roles:
            await interaction.user.add_roles(role)

        # Report back on our success!
        await interaction.response.edit_message(
            content=f"Added the {str(role_strings).strip('[]')} roles to {interaction.user.mention}",
            view=self,
        )


def setup(bot: commands.Bot):
    bot.add_cog(PlayerInfoCog(bot))
