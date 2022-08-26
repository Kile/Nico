import discord
from discord.ext import commands

from bot.utils.interactions import Modal
from bot.static.constants import GUILD_OBJECT

class TrialsModal(Modal):

    def __init__(self, user_id: int):
        super().__init__(user_id, title="Trial Application form")
        
        self.add_item(discord.ui.TextInput(label="What position do you want to trial for?", placeholder="Moderator/Server Manager/Both", style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(label="How often are you on discord?", placeholder="1h a day/whenever I can/on weekends/...", style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(label="What makes you qualified for that position?", placeholder="I am qualified to be ... because ...", required=True, max_length=4000, min_length=20, style=discord.TextStyle.long))

class Trials(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        
    @property
    def guild(self) -> discord.Guild:
        return self.client.get_guild(self.client.server_info.ID)

    @property
    def channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.TRIAL_APS_CHANNEL)

    async def cog_load(self):
        print("Loaded trials cog")

    @discord.app_commands.command()
    @discord.app_commands.guilds(GUILD_OBJECT)
    async def trials(self, interaction: discord.Interaction):
        """Apply for trials with this command"""
    
        modal = TrialsModal(interaction.user.id)
        await interaction.response.send_modal(modal)
        await modal.wait()
    
        poition = modal.children[0].value
        online_when = modal.children[1].value
        application = modal.children[2].value
        embed = discord.Embed(title="Application", description=application, color=0x2f3136)
        embed.add_field(name="Position", value=poition)
        embed.add_field(name="User", value=interaction.user.mention)
        embed.add_field(name="Online when", value=online_when)
        embed.set_thumbnail(url=interaction.user.avatar.url)
        await self.channel.send(embed=embed)
        await modal.interaction.response.send_message("Thank you for your application!", ephemeral=True)

Cog = Trials