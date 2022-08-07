import discord

from discord.ext import commands
from datetime import datetime

from bot.static.constants import PARTNERS

class Partners(commands.Cog):

    def __init__(self, client):
        self.client = client

    @property
    def guild(self):
        return self.client.get_guild(self.client.server_info.ID)

    @property
    def channel(self):
        return self.guild.get_channel(self.client.server_info.GENERAL_CHANNEL)

    @property
    def potato_channel(self):
        return self.guild.get_channel(self.client.server_info.POTATO_BONUS_CHANNEL)

    async def cog_load(self):
        print("Loaded partners cog")

    partner = discord.app_commands.Group(name='partner', description="Commands related to partnerships")

    @partner.command()
    @discord.app_commands.describe(partner_invite="The invite link of the partner server")
    async def new(self, interaction: discord.Interaction, partner_invite: str):
        """Register a new partnership and get the url to send them."""
        if self.client.server_info.PARTNER_MANAGER_ROLE in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("You need to be a partner manager to use this command.", ephemeral=True)

        try:
            invite = await self.client.fetch_invite(partner_invite)
        except discord.NotFound:
            return await interaction.response.send_message("Invalid invite link.", ephemeral=True)

        if invite.expires_at:
            return await interaction.response.send_message("The invite link has to be permanent, this one is temporary.", ephemeral=True)

        guild_invite = await self.channel.create_invite(reason="New partner")

        data = {
            "added_on": datetime.now(),
            "added_by": interaction.user.id,
            "partner_invite_link": partner_invite,
            "own_invite_link": guild_invite.url
        }

        PARTNERS.insert_one(data)
        await interaction.response.send_message(f"Your partner invite link is: {guild_invite.url}", ephemeral=True)
        await self.potato_channel.send(f"{interaction.user.mention} has registered a new partnership with {invite.guild.name}. They will be awarded a bonus of 10🥔")

    @partner.command()
    async def top(self, interaction: discord.Interaction):
        """Displays the top 10 partners in terms of new joins"""
        partners = list(PARTNERS.find())
        invites = await self.guild.invites()

        for partner in partners:
            for invite in invites:
                if invite.code == partner["own_invite_link"] or invite.url == partner["own_invite_link"]:
                    partner["uses"] = invite.uses

        top_partners = sorted(partners, key=lambda x: x["uses"], reverse=True)[:10]

        embed = discord.Embed(title="Top 10 Partners", color=0x2f3136)

        for partner in top_partners:
            partner_invite = await self.client.fetch_invite(partner["partner_invite_link"])
            
            embed.add_field(
                name=partner_invite.guild.name, 
                value="Joins: " + str(partner["uses"]) + "\n" + 
                "PM responsible: " + str(self.client.get_user(partner["added_by"])),
        )

        await interaction.response.send_message(embed=embed)

    @partner.command()
    @discord.app_commands.describe(user="The user to check the partners of")
    async def user(self, interaction: discord.Interaction, user: discord.Member):
        """Lists the number of partners a user has added"""
        partners = list(PARTNERS.find({"added_by": user.id}))

        await interaction.response.send_message(f"{user.name} has added {len(partners)} partner{'s' if len(partners) != 1 else ''}.")

Cog = Partners

async def setup(client):
    await client.add_cog(Partners(client))