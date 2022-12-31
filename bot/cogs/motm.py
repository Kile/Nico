import discord
from discord.ext import commands, tasks

from datetime import datetime, timedelta
from typing import List
from random import choice

from bot.__init__ import Bot
from bot.static.constants import MOTM, MOTM_VOTE_LIMIT, CONSTANTS
from bot.utils.interactions import Modal

class MemberOfTheMonth(commands.Cog):

    def __init__(self, client: Bot):
        self.client = client

    async def cog_load(self):
        print("Loaded motm cog")

    motm = discord.app_commands.Group(name="motm", description="Commands relating to the member of the month")

    @property
    def guild(self) -> discord.Guild:
        return self.client.get_guild(self.client.server_info.ID)

    def __num_of_votes(self, member: discord.Member) -> int:
        """Checks the amount of people a member has voted for this month"""
        all_members: List[dict] = MOTM.find({})

        members_voted_for_this_month = 0

        for m in all_members:
            for key, value in m.items():

                try:
                    date = datetime.fromisoformat(key)
                except ValueError:
                    continue

                if date.month == datetime.now().month and date.year == datetime.now().year:
                    if member.id in value:
                        members_voted_for_this_month += 1

        return members_voted_for_this_month

    def _vote(self, voter: discord.Member, voted_for: discord.Member) -> int:
        """Vote for a member of the month. Returns the number of votes the member has this month"""

        # First try to find weather there is a document for this month
        data: dict = MOTM.find_one({"_id": voted_for.id})

        if not data:
            MOTM.insert_one({"_id": voted_for.id, datetime.now().isoformat(): [voter.id]})
            return 1

        last_vote_month = datetime.fromisoformat(data.keys()[-1])

        if last_vote_month.month == datetime.now().month and last_vote_month.year == datetime.now().year:
            MOTM.update_one({"_id": voted_for.id}, {"$push": {last_vote_month.isoformat(): voter.id}})
            return len(data[last_vote_month.isoformat()]) + 1
        else:
            MOTM.update_one({"_id": voted_for.id}, {"$set": {datetime.now().isoformat(): [voter.id]}})
            return 1

    @motm.command()
    async def suggest(self, interaction: discord.Interaction, member: discord.Member):
        """Suggest a member of the month"""

        if (n := self.__num_of_votes(interaction.user)) >= MOTM_VOTE_LIMIT:
            return await interaction.response.send_message(f"You have already voted for {n}/{MOTM_VOTE_LIMIT} members this month!", ephemeral=True)

        # Check if a motm has already been chosen this month
        if (_data := CONSTANTS.find_one({"_id": "motm"})) and (_date := datetime.fromisoformat(_data["date"])).month == datetime.now().month and _date.year == datetime.now().year:
            return await interaction.response.send_message("A member of the month has already been chosen this month!", ephemeral=True)

        if member == interaction.user:
            return await interaction.response.send_message("You can't suggest yourself! (lol nice try)", ephemeral=True)

        member_data = MOTM.find_one({"_id": member.id})
        if member_data:
            if interaction.user.id in list(member_data.values())[-1] and datetime.fromisoformat(list(member_data.keys())[-1]).month == datetime.now().month and datetime.fromisoformat(list(member_data.keys())[-1]).year == datetime.now().year:
                return await interaction.response.send_message("You have already voted for this member this month!", ephemeral=True)

        modal = Modal(title="Suggest a member of the month")
        reason = discord.ui.TextInput(label="Why should this member be motm?", placeholder="This member should be motm because...", required=True, max_length=4000, min_length=20, style=discord.TextStyle.long)
        modal.add_item(reason)

        await interaction.response.send_modal(modal)

        await modal.wait()

        embed = discord.Embed(title="Member of the month suggestion", description=reason.value, color=0x2f3136, timestamp=discord.utils.utcnow())
        embed.add_field(name="Suggested by", value=interaction.user.mention)
        embed.add_field(name="Suggested member", value=member.mention)
        embed.set_thumbnail(url=member.avatar.url)
        votes = self._vote(interaction.user, member)
        embed.set_footer(text=f"This member recieved {votes} votes this month")

        await self.client.get_channel(self.client.server_info.MOTM_SUGGESTION_CHANNEL).send(embed=embed)

        await modal.interaction.response.send_message("Your suggestion has been sent!", ephemeral=True)

    @motm.command()
    async def colour(self, interaction: discord.Interaction, colour: str):
        """Change the colour of the member of the month role"""

        if not self.client.server_info.MOTM in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("You need to be the current member of the month to do this!", ephemeral=True)

        try:
            colour = int(colour, 16)
        except ValueError:
            return await interaction.response.send_message("Invalid colour! It needs to be a hexadecimal integer!", ephemeral=True)

        role = interaction.guild.get_role(self.client.server_info.MOTM)
        await role.edit(colour=discord.Colour(colour))

        await interaction.response.send_message("The colour of the member of the month embed has been changed!", ephemeral=True)

    @tasks.loop(hours=12)
    async def crown_motm(self):
        """Crown the member of the month"""
        # Do not crown if there is already a member of the month
        last_winner_data = CONSTANTS.find_one({"_id": "motm"})
        if last_winner_data:
            if len(last_winner_data["winners"]) > 0:
                last_winner_month = datetime.fromisoformat(last_winner_data["winners"][-1]["date"])
                now = datetime.now() - timedelta(days=3) # Give a recommendation 3 days before the end of the month
                if last_winner_month.month == now.month and last_winner_month.year == now.year:
                    return

        # First get the member with the most votes this month
        # However ignore the member if they had the most votes last month
        # If there is a tie, the winner is randomly chosen

        all_members: List[dict] = MOTM.find({})

        members_voted_for_this_month = {}

        for member in all_members:
            for key, value in member.items():

                try:
                    date = datetime.fromisoformat(key)
                except ValueError:
                    continue

                if date.month == datetime.now().month and date.year == datetime.now().year:
                    members_voted_for_this_month[member["_id"]] = len(value)

        if not members_voted_for_this_month:
            return

        most_votes = max(members_voted_for_this_month.values())

        # find the member with most votes who didn't have the most votes last month
        if not last_winner_data:
            last_winner = None
        elif len(last_winner_data["winners"]) == 0:
            last_winner = None
        else:
            last_winner = CONSTANTS.find_one({"_id": "motm"})["winners"][-1]["member"]

        members_with_most_votes = [member for member, votes in members_voted_for_this_month.items() if votes == most_votes and member != last_winner]

        if not members_with_most_votes:
            return

        winner = choice(members_with_most_votes)

        # Now suggest winner in MOTM channel
        member = self.guild.get_member(winner)
        embed = discord.Embed(title="\U0001f451 Member of the month recommendation", description=f"Suggestion this month: {member.mention}\n\nThey have recieved {members_voted_for_this_month[member.id]} votes this month.", color=discord.Color.yellow, timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=member.avatar.url)

        message = await self.client.get_channel(self.client.server_info.MOTM_SUGGESTION_CHANNEL).send(embed=embed)
        # Pin the message
        await message.pin()

    @motm.command()
    async def crown(self, interaction: discord.Interaction, member: discord.Member):
        """Crown the member of the month"""

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("You need to be an administrator to do this!", ephemeral=True)

        # Add member to database of past winners
        CONSTANTS.update_one({"_id": "motm"}, {"$push": {"winners": {"member": member.id, "date": (datetime.now() - timedelta(days=7)).isoformat()}}})

        # Remove motm role from everyone
        role = interaction.guild.get_role(self.client.server_info.MOTM)
        for member in role.members:
            await member.remove_roles(role)

        # Give member the member of the month role
        await member.add_roles(role)

        await interaction.response.send_message("The member of the month has been crowned! \U0001f451", ephemeral=True)

Cog = MemberOfTheMonth