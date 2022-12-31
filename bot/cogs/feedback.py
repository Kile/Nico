import discord
from discord.ext import commands

from bot.__init__ import Bot
from bot.utils.interactions import Modal
from bot.static.constants import GUILD_OBJECT
from bot.utils.classes import PotatoMember as Member

class Feedback(commands.Cog):

    def __init__(self, client: Bot):
        self.client = client
        
    @property
    def guild(self) -> discord.Guild:
        return self.client.get_guild(self.client.server_info.ID)

    @property
    def channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.FEEDBACK_CHANNEL)

    @property
    def potato_channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.POTATO_BONUS_CHANNEL)

    async def cog_load(self):
        print("Loaded feedback cog")

    @discord.app_commands.command()
    @discord.app_commands.guilds(GUILD_OBJECT)
    async def feedback(self, interaction: discord.Interaction):
        """Submit feedback about the server with this command"""
    
        modal = Modal()
        _feedback = discord.ui.TextInput(label="Feedback", placeholder="I think that the server needs.../I like that the server has...", required=True, max_length=4000, min_length=20, style=discord.TextStyle.long)
        modal.add_item(_feedback)

        await interaction.response.send_modal(modal)

        await modal.wait()
    
        embed = discord.Embed(title="Feedback", description=_feedback, color=0x2f3136)
        embed.set_footer(text=f"Submitted by {interaction.user}")
        await self.channel.send(embed=embed)
        Member(interaction.user).add_potatoes(5)
        await self.potato_channel.send(f"{interaction.user.mention} has left given feedback with `/feedback`. They have been awarded a bonus of 5🥔")
        await modal.interaction.response.send_message("Thank you for your feedback!", ephemeral=True)

Cog = Feedback