import discord

from discord.ext import commands

from bot.static.constants import GUILD_OBJECT, DID_INFO

class Various(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    async def cog_load(self):
        print("Loaded various cog")

    @property
    def guild(self) -> discord.Guild:
        return self.client.get_guild(self.client.server_info.ID)

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