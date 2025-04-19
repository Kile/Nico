import discord
from discord.ext import commands
from bot.__init__ import Bot

from datetime import timedelta

TAG_ROLE = 1362726731768922205

class Tag(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    async def cog_load(self):
        print("Loaded tag cog")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.data.get("custom_id") != "full_access":
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # If they have been in the server for less than 24 hrs, say no
        if interaction.user.joined_at > discord.utils.utcnow() - timedelta(hours=24):
            return await interaction.followup.send("You need to be in the server for at least 24 hours to get full access.", ephemeral=True)
        
        # remove the tag role
        if TAG_ROLE in [r.id for r in interaction.user.roles]:
            await interaction.user.remove_roles(interaction.guild.get_role(TAG_ROLE))
            return await interaction.followup.send("You have been granted access to the server.", ephemeral=True)
        else:
            return await interaction.followup.send("You already have server access bro", ephemeral=True)
        
    # Add tag role on join
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        return # TEMPORARILY DISABLED
        if member.guild.id != self.client.server_info.ID: return # Don't want that process when someone is joining on another server

        if member.bot: return

        await member.add_roles(member.guild.get_role(TAG_ROLE))

Cog = Tag