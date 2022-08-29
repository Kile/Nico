import discord

from discord.ext import commands

from datetime import datetime, timedelta, timezone

from bot.static.constants import GUILD_OBJECT, DID_INFO, CONSTANTS

class Various(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    async def cog_load(self):
        print("Loaded various cog")

    @property
    def guild(self) -> discord.Guild:
        return self.client.get_guild(self.client.server_info.ID)

    @property
    def chat_revive(self) -> discord.Role:
        return self.guild.get_role(self.client.server_info.CHAT_REVIVE_ROLE)

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

    @discord.app_commands.command()
    @discord.app_commands.guilds(GUILD_OBJECT)
    async def revive(self, interaction: discord.Interaction):
        """Pings the "chat revive" role. Only usable every 2 hours by a member with the verified role."""

        if not self.client.server_info.VERIFIED_ROLE in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("You are not verified! Get verified with `/apply`", ephemeral=True)

        if interaction.channel.id != self.client.server_info.GENERAL_CHANNEL:
            return await interaction.response.send_message(f"You can only use this command in <#{self.client.server_info.GENERAL_CHANNEL}>", ephemeral=True)

        data = CONSTANTS.find_one({"_id": "chat_revive"})

        if data and (datetime.now() - data["last_ping"]) < timedelta(hours=2):
            return await interaction.response.send_message(f"You can only ping the chat revive role every 2 hours. You can next ping it <t:{int((data['last_ping'] + timedelta(hours=2)).timestamp())}:R>", ephemeral=True)

        counter = 0
        messangers = []

        async for message in interaction.channel.history(limit=10, after=datetime.now() - timedelta(minutes=2)):
            counter += 1
            if message.author.id not in messangers:
                messangers.append(message.author.id)

        if counter == 10 and len(messangers) > 2:
            return await interaction.response.send_message(f"The chat is currently too active to ping the chat revive role!", ephemeral=True)

        if data:
            CONSTANTS.update_one({"_id": "chat_revive"}, {"$set": {"last_ping": datetime.now(), "last_ping_by": interaction.user.id}})
        else:
            CONSTANTS.insert_one({"_id": "chat_revive", "last_ping": datetime.now(), "last_ping_by": interaction.user.id})
        await interaction.response.send_message(f"{interaction.user.mention} calls upon the mighty {self.chat_revive.mention}!")

    @discord.app_commands.command()
    @discord.app_commands.guilds(GUILD_OBJECT)
    async def close(self, interaction: discord.Interaction):
        """Closes the current help thread"""

        if not isinstance(interaction.channel, discord.Thread):
            return await interaction.response.send_message("This command can only be used in a thread", ephemeral=True)

        if not interaction.user.id == interaction.channel.owner_id or self.client.server_info.WILL_HELP_ROLE in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(f"You can only use this thread if you have the <@&{self.client.server_info.WILL_HELP_ROLE}> role or are the thread creator.", ephemeral=True)

        await interaction.response.send_message(f"{interaction.user.mention} has closed this thread.")
        await interaction.channel.edit(archived=True, locked=True if self.client.server_info.TRUSTED_ROLE else False)

Cog = Various