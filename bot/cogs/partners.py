import discord

from discord.ext import commands
from datetime import datetime

from bot.__init__ import Bot
from bot.static.constants import PARTNERS, GUILD_OBJECT
from bot.utils.classes import PotatoMember as Member

class Partners(commands.Cog):

    def __init__(self, client: Bot):
        self.client = client

    @property
    def guild(self) -> discord.Guild:
        return self.client.get_guild(self.client.server_info.ID)

    @property
    def channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.GENERAL_CHANNEL)

    @property
    def potato_channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.POTATO_BONUS_CHANNEL)

    async def cog_load(self):
        print("Loaded partners cog")

    partner = discord.app_commands.Group(name='partner', description="Commands related to partnerships", guild_ids=[GUILD_OBJECT.id])

    @partner.command()
    @discord.app_commands.describe(partner_invite="The invite link of the partner server")
    async def new(self, interaction: discord.Interaction, partner_invite: str):
        """Register a new partnership and get the url to send them."""
        if not self.client.server_info.PARTNER_MANAGER_ROLE in [r.id for r in interaction.user.roles]:
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
        Member(interaction.user.id).add_potatoes(10)
        await self.potato_channel.send(f"{interaction.user.mention} has registered a new partnership with {invite.guild.name}. They have been awarded a bonus of 10🥔")

    @partner.command()
    async def top(self, interaction: discord.Interaction):
        """Displays the top 10 partners in terms of new joins"""
        await interaction.response.defer() # This command will take more than 3 seconds most likely so we want to make sure discord knows that
        partners = list(PARTNERS.find())
        invites = await self.guild.invites()

        for partner in partners:
            for invite in invites:
                if invite.code == partner["own_invite_link"] or invite.url == partner["own_invite_link"]:
                    partner["uses"] = invite.uses

        top_partners = sorted(partners, key=lambda x: x["uses"], reverse=True)[:10]

        embed = discord.Embed(title="Top 10 Partners", color=0x2f3136)

        for partner in top_partners:
            try:
                partner_invite = await self.client.fetch_invite(partner["partner_invite_link"])
            except discord.NotFound:
                partner_invite = "Invalid invite"
            
            embed.add_field(
                name=partner_invite.guild.name if not isinstance(partner_invite, str) else partner_invite, 
                value="Joins: " + str(partner["uses"]) + "\n" + 
                "PM responsible: " + self.client.get_user(partner["added_by"]).display_name,
        )

        await interaction.followup.send(embed=embed)

    @partner.command()
    @discord.app_commands.describe(user="The user to check the partners of")
    async def user(self, interaction: discord.Interaction, user: discord.Member):
        """Lists the number of partners a user has added"""
        partners = list(PARTNERS.find({"added_by": user.id}))

        await interaction.response.send_message(f"{user.name} has added {len(partners)} partner{'s' if len(partners) != 1 else ''}.")

    @partner.command()
    @discord.app_commands.describe(
        nss_invite="The invite to Nico's Safe Space used for the partnership",
        new_invite="The new invite to the partner server"
    )
    async def update(self, interaction: discord.Interaction, nss_invite: str, new_invite: str):
        """Updates the invite of a partner"""
        if not self.client.server_info.PARTNER_MANAGER_ROLE in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("You need to be a partner manager to use this command.", ephemeral=True)

        try:
            invite = await self.client.fetch_invite(new_invite)
        except discord.NotFound:
            return await interaction.response.send_message("Invalid invite link.", ephemeral=True)

        if invite.expires_at:
            return await interaction.response.send_message("The invite link has to be permanent, this one is temporary.", ephemeral=True)

        if not nss_invite in [inv.url if "discord.gg" in nss_invite else inv.code for inv in await self.guild.invites()]:
            return await interaction.response.send_message("Invalid NSS invite link.", ephemeral=True)

        PARTNERS.update_one({"own_invite_link": nss_invite}, {"$set": {"partner_invite_link": new_invite}})

        await interaction.response.send_message(f"Successfully updated invite link for {invite.guild.name}.", ephemeral=True)

    @partner.command()
    @discord.app_commands.describe(nss_invite="The invite to Nico's Safe Space used for the partnership")
    async def delete(self, interaction: discord.Interaction, nss_invite: str):
        """Deletes a partner"""
        if not self.client.server_info.PARTNER_MANAGER_ROLE in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("You need to be a partner manager to use this command.", ephemeral=True)

        if not nss_invite in [inv.url if "discord.gg" in nss_invite else inv.code for inv in await self.guild.invites()]:
            return await interaction.response.send_message("Invalid NSS invite link.", ephemeral=True)

        PARTNERS.delete_one({"own_invite_link": nss_invite})

        await interaction.response.send_message(f"Successfully deleted partner with invite: {nss_invite}.", ephemeral=True)

Cog = Partners