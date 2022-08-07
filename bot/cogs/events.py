import discord

from discord.ext import commands

from bot.static.constants import DISBOARD, WELCOME_MESSAGE

class Events(commands.Cog):

    def __init__(self, client):
        self.client = client

    @property
    def guild(self):
        return self.client.get_guild(self.client.server_info.ID)

    @property
    def potato_channel(self):
        return self.guild.get_channel(self.client.server_info.POTATO_BONUS_CHANNEL)

    @property
    def general_channel(self):
        return self.guild.get_channel(self.client.server_info.GENERAL_CHANNEL)

    async def cog_load(self):
        print("Loaded application cog")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id != DISBOARD:
            return

        if len(message.embeds) > 0 and ":thumbsup:" in message.embeds[0].description:
            await self.potato_channel.send(f"{message.interaction.user.mention} has bumped the server! They will be awarded a bonus of 2🥔")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot: return

        await self.general_channel.send(WELCOME_MESSAGE.format(member.mention))

Cog = Events

async def setup(self):
    await self.add_cog(Events(self))