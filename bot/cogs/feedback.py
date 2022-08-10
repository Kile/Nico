import discord
from discord.ext import commands

from bot.utils.interactions import Modal
from bot.static.constants import GUILD_OBJECT

class FeedbackModal(Modal):

    def __init__(self, user_id: int):
        super().__init__(user_id, title="Feedback form")
        
        self.add_item(discord.ui.TextInput(label="Feedback", placeholder="I think that the server needs.../I like that the server has...", required=True, max_length=4000, min_length=20, style=discord.TextStyle.long))

class Feedback(commands.Cog):

    def __init__(self, client):
        self.client = client
        
    @property
    def guild(self):
        return self.client.get_guild(self.client.server_info.ID)

    @property
    def channel(self):
        return self.guild.get_channel(self.client.server_info.FEEDBACK_CHANNEL)

    @property
    def potato_channel(self):
        return self.guild.get_channel(self.client.server_info.POTATO_BONUS_CHANNEL)

    async def cog_load(self):
        print("Loaded application cog")

    @discord.app_commands.command()
    @discord.app_commands.guilds(GUILD_OBJECT)
    async def feedback(self, interaction: discord.Interaction):
        """Submit feedback about the server with this command"""
    
        modal = FeedbackModal(interaction.user.id)
        await interaction.response.send_modal(modal)
        await modal.wait()
    
        feedback = modal.children[0].value
        embed = discord.Embed(title="Feedback", description=feedback, color=0x2f3136)
        embed.set_footer(text=f"Submitted by {interaction.user}")
        await self.channel.send(embed=embed)
        await self.potato_channel.send(f"{interaction.user.mention} has left given feedback with `/feedback`. They have been awarded a bonus of 5🥔")
        await modal.interaction.response.send_message("Thank you for your feedback!", ephemeral=True)

Cog = Feedback

async def setup(client):
    await client.add_cog(Feedback(client))