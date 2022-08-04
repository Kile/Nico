import discord
from discord.ext import commands

from typing import Optional, Any

from bot.utils.interactions import View, Button
from bot.static.constants import Sexualities, OtherRoles

Choice = discord.app_commands.Choice

class Roles(commands.Cog):

    # These need to be strings thanks to discord

    _pronouns = [
        Choice(name="any pronouns", value="1004866171083956346"),
        Choice(name="he/him", value="731460738433941574"),
        Choice(name="she/her", value="731460795912814664"),
        Choice(name="they/them", value="731460788006682675"),
        Choice(name="he/they", value="1004866230395617391"),
        Choice(name="she/they", value="1004866278084841613"),
        Choice(name="it/its", value="1004866337602023534"),
        Choice(name="name only", value="1004866388617347194"),
        Choice(name="ask for pronouns", value="733341659860959304")
    ]

    _dm_options = [
        Choice(name="open dms", value="804874288434774026"),
        Choice(name="closed dms", value="804861287703380039"),
        Choice(name="ask to dm", value="804879802611662898")
    ]

    _help_roles = [
        Choice(name="will help", value="712375696642801854"),
        Choice(name="vent access", value="743963300060069958"),
        Choice(name="advice access", value="743963359946473552"),
        Choice(name="need help", value="712372007399849985")
    ]

    def __init__(self, client):
        self.client = client
        
    @property
    def guild(self):
        return self.client.get_guild(self.client.server_info.ID)

    def intercept(list1: list, list2: list) -> Optional[Any]:
        """Checks if two lists have any common items"""
        for item in list1:
            if item in list2:
                return item
        return False

    async def cog_load(self):
        print("Loaded roles cog")

    roles = discord.app_commands.Group(name='roles', description="Assign yourself a role")

    @roles.command()
    @discord.app_commands.describe(sexuality="Your sexuality")
    async def sexuality(self, interaction: discord.Interaction, sexuality: Sexualities):
        """Choose what sexuality role to assign yourself"""
        if (intercept := self.intercepts([r.id for r in interaction.user.roles], [int(r.value) for r in Sexualities])):
            await interaction.user.remove_role(self.guild.get_role(intercept))
            # You can only have one sexuality role, so it removes your current one
        
        await interaction.user.add_role(self.guild.get_role(int(sexuality.value)))
        await interaction.response.send_message(f"You have been assigned the {sexuality.name} role!")

    @roles.command()
    @discord.app_commands.choices(
        pronouns=_pronouns
    )
    @discord.app_commands.describe(pronouns="The pronouns you want to use")
    async def pronouns(self, interaction: discord.Interaction, pronouns: Choice[str]):
        """Choose what pronouns role to assign yourself"""
        if (intercept := self.intercepts([r.id for r in interaction.user.roles], [int(x.value) for x in self._pronouns])):
            await interaction.user.remove_role(self.guild.get_role(intercept))
            # You can only have one pronouns role, so it removes your current one
        
        await interaction.user.add_role(self.guild.get_role(int(pronouns.value)))
        await interaction.response.send_message(f"You have been assigned the {pronouns.name} role!")

    @roles.command()
    @discord.app_commands.choices(
        option=_dm_options
    )
    @discord.app_commands.describe(option="The option you want to use")
    async def dms(self, interaction: discord.Interaction, option: Choice[str]):
        """Choose if you want to recieve dms from others or not"""
        if (intercept := self.intercepts([r.id for r in interaction.user.roles], [int(x.value) for x in self._dm_options])):
            await interaction.user.remove_role(self.guild.get_role(intercept))
            # You can only have one dms role, so it removes your current one

        await interaction.user.add_role(self.guild.get_role(int(option.value)))
        await interaction.response.send_message(f"You have been assigned the {option.name} role!")

    @roles.command()
    @discord.app_commands.describe(role="The role you want to assign yourself")
    async def other(self, interaction: discord.Interaction, role: OtherRoles):
        """Choose one of the various interets roles"""
        if int(role.value) in [r.id for r in interaction.user.roles]:
            await interaction.user.remove_role(self.guild.get_role(int(role.value)))
            # This means the user wants to remove the role
            return await interaction.response.send_message(f"You have been removed the {role.name} role!")
        else:
            await interaction.user.add_role(self.guild.get_role(role))
            return await interaction.response.send_message(f"You have been assigned the {role.name} role!")

    @roles.command()
    @discord.app_commands.choices(
        role=_help_roles
    )
    @discord.app_commands.describe(role="The role you want to assign yourself")
    async def help(self, interaction: discord.Interaction, role: Choice[str]):
        """Choose one of the various help roles"""
        if int(role.value) in [r.id for r in interaction.user.roles]:
            await interaction.user.remove_role(self.guild.get_role(int(role.value)))
            # This means the user wants to remove the role
            return await interaction.response.send_message(f"You have been removed the {role.name} role!")
        else:
            if role.name == "need help":
                confirm_button = Button(label="Confirm", style=discord.ButtonStyle.green, custom_id="confirm")
                cancel_button = Button(label="Cancel", style=discord.ButtonStyle.red, custom_id="cancel")
                view = View(interaction.user.id)
                view.add_item(confirm_button)
                view.add_item(cancel_button)
                await interaction.response.send_message("By choosing this role you signal that you need **immediate** serious help. This will ping the will help role. Do you want to proceed?", view=view, ephemeral=True)

                await view.wait()

                if view.timed_out:
                    return 
                else:
                    if view.value == "cancel":
                        return await view.interaction.response.send_message("You have successfully cancelled. Have a great rest of your day.", ephemeral=True)
                    else:
                        sos_channel = self.guild.get_channel(self.client.server_info.SOS_CHANNEL)
                        await sos_channel.send(f"{interaction.user.mention} could use some help <@&712375696642801854>")

            await interaction.user.add_role(self.guild.get_role(int(role.value)))
            return await interaction.response.send_message(f"You have been assigned the {role.name} role!")

Cog = Roles

async def setup(client):
    await client.add_cog(Roles(client))