import discord

from discord.ext import commands

from bot.static.constants import GUILD_OBJECT, DID_INFO
from bot.utils.interactions import Modal

class UpdateModal(Modal):

    def __init__(self, user_id: int):
        super().__init__(user_id, title="Update")
        self.add_item(discord.ui.TextInput(label="What's new?", placeholder="Made Nico event better (although impossible)", required=True, max_length=4000, style=discord.TextStyle.long))

class Various(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        self.update_banner_url = "https://cdn.discordapp.com/attachments/1004512555538067476/1008487606893416538/20220814_234634_0000.png"

    async def cog_load(self):
        print("Loaded various cog")

    @property
    def guild(self) -> discord.Guild:
        return self.client.get_guild(self.client.server_info.ID)

    @property
    def update_channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.UPDATE_CHANNEL)

    @discord.app_commands.command()
    @discord.app_commands.guilds(GUILD_OBJECT)
    async def update(self, interaction: discord.Interaction):
        """Submit an update about Nico with this command"""
        if not interaction.user.id == self.guild.owner_id:
            return await interaction.response.send_message("You must be the server owner to use this command", ephemeral=True)

        modal = UpdateModal(interaction.user.id)
        await interaction.response.send_modal(modal)
        await modal.wait()

        update = modal.children[0].value
        embed = discord.Embed.from_dict({
            "title": "**New Nico update**",
            "description": update,
            "color": 0xfbafaf,
            "image": {
                "url": self.update_banner_url
            },
        })
        await self.update_channel.send(embed=embed)
        await modal.interaction.response.send_message(":white_check_mark: Update published!", ephemeral=True)

    @discord.app_commands.command()
    @discord.app_commands.guilds(GUILD_OBJECT)
    async def did(self, interaction: discord.Interaction):
        """Gives you an explenation of did, short for Dissociative Identity Disorder"""

        embed = discord.Embed.from_dict({
            "title": "What is DID?",
            "description": DID_INFO,
            "color": 0x2f3136
        })

        await interaction.response.send_message(embed=embed)

Cog = Various