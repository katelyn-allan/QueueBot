import discord
from discord import ApplicationContext
import commands.player_stats as player_stats
from util.exceptions import *
from typing import List, Dict
from discord.ext import commands
from util.env_load import *


class PlayerInfoCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: discord.Bot = bot

    def convert_stat_dict_to_str_output(self, stats: Dict[str, float]) -> str:
        """Converts a player stats dict into a string output for reporting."""
        output = ""
        for key, value in stats.items():
            output += f"**{key.replace('_', ' ').capitalize()}:** {value}\n"
        return output

    @discord.slash_command(name="stats", description="Get your stats")
    async def slash_get_stats(self, ctx: ApplicationContext):
        stats: Dict[str, Dict[str, float]] = player_stats.get_player_stats(ctx)
        embed = discord.Embed(
            title="Player Stats",
            color=discord.Colour.blurple(),
            description=f"Stats for {ctx.user.mention}",
        )
        embed.add_field(
            name=f"Tank {TANK_EMOJI}",
            value=self.convert_stat_dict_to_str_output(stats["tank"]),
            inline=False,
        )
        embed.add_field(
            name=f"Support {SUPPORT_EMOJI}",
            value=self.convert_stat_dict_to_str_output(stats["support"]),
            inline=False,
        )
        embed.add_field(
            name=f"Assassin {ASSASSIN_EMOJI}",
            value=self.convert_stat_dict_to_str_output(stats["assassin"]),
            inline=False,
        )
        embed.add_field(
            name=f"Offlane {OFFLANE_EMOJI}",
            value=self.convert_stat_dict_to_str_output(stats["offlane"]),
            inline=False,
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.respond(embed=embed, ephemeral=True)

    @discord.slash_command(name="setup", description="Get set up with the Queue Bot!")
    async def slash_setup(self, ctx: ApplicationContext):
        main_role_view = MainRoleSelectView()
        await ctx.respond(
            "Select your main role. Your main role will always be prioritized for match-making when possible.",
            view=main_role_view,
            ephemeral=True,
        )
        await main_role_view.wait()
        user_roles = ctx.user.roles
        main_role = None
        for role in user_roles:
            if role.name in ["Tank", "Support", "Assassin", "Offlane"]:
                main_role = role.name
        await ctx.respond(
            "Select your secondary roles. These will be used to fill out the rest of the team when your main role is not available.",
            view=SecondaryRoleSelectView(main_role=main_role),
            ephemeral=True,
        )


class MainRoleSelectView(discord.ui.View):
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
    async def main_role_callback(self, select: discord.SelectMenu, interaction: discord.Interaction):
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
        self.stop()


class SecondaryRoleSelectView(discord.ui.View):
    def __init__(self, main_role: str) -> None:
        super().__init__()
        self.main_role = main_role

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
    async def secondary_role_callback(self, select: discord.SelectMenu, interaction: discord.Interaction):
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
        main_role_fill = f"{self.main_role} (Fill)"
        if main_role_fill in role_strings:
            role_strings.remove(main_role_fill)
        roles: List[discord.Role] = [discord.utils.get(interaction.guild.roles, name=role_string) for role_string in role_strings]
        for role in roles:
            await interaction.user.add_roles(role)

        # Report back on our success!
        await interaction.response.edit_message(
            content=f"Added the {str(role_strings).strip('[]')} roles to {interaction.user.mention}",
            view=self,
        )


def setup(bot: commands.Bot):
    bot.add_cog(PlayerInfoCog(bot))
