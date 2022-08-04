import discord
from discord.ext import commands

from typing import Union
from asyncio import sleep, TimeoutError

from bot.utils.interactions import Modal, View, Button
from bot.static.constants import QUESTIONS

class ApplicationModal(Modal):

    def __init__(self, user_id: int, page: int):
        super().__init__(user_id, title="Application")
        if page == 1:
            questions = QUESTIONS[:5]
        elif page == 2:
            questions = QUESTIONS[5:10]
        else:
            questions = QUESTIONS[:-2]

        for question in questions:
            self.add_item(discord.ui.TextInput(label=question["question"], placeholder=question["placeholder"], required=question["required"], max_length=question["max_length"]))

class Application(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def cog_load(self):
        print("Loaded application cog")

    def _to_embed(self, user: Union[discord.Member, discord.User], responses: list) -> discord.Embed:
        embed = discord.Embed.from_dict({
            "title": f"Application of {user.name}",
            "description": user.mention,
            "fields": [{"name": QUESTIONS[i], "value": responses[i] or "N/A"} for i in range(len(responses))],
            "color": 0x2f3136,
            "thumbnail": {
                "url": user.avatar.url if user.avatar else None
            }
        })
        return embed

    @discord.app_commands.command()
    async def apply(self, interaction: discord.Interaction):
        """Apply for the verified role with this command"""

        if self.client.server_info.VERIFIED_ROLE in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("You are already verified!", ephemeral=True)

        if interaction.user.is_on_mobile():
            return await interaction.response.send_message("Due to a discord limitation this command is currently not available on mobile. Please use `/mobile_apply` instead!", ephemeral=True)

        answers = []

        for i in range(1, 4):
            modal = ApplicationModal(interaction.user.id, i)
            await interaction.response.send_modal(modal)
            await modal.wait()

            if modal.timed_out:
                return
            else:
                answers = [*answers, *modal.values]

                if i < 3:
                    button = Button(label="Continue", style=discord.ButtonStyle.green)
                    view = View(interaction.user.id)
                    view.add_item(button)
                    msg = await interaction.channel.send(f"Application completed {i}/3. Press continue to continue.", view=view)
                    await view.wait()
                    
                    if view.timed_out:
                        await interaction.channel.send("Not responded in time. Application cancelled.")
                    else:
                        await msg.delete()
                        i += 1
                        interaction = view.interaction

        channel = self.client.get_channel(self.client.server_info.APPLICATION_CHANNEL)
        await channel.send(embed=self._to_embed(interaction.user, answers))
        await interaction.channel.send("✅ Application submitted. Please be patient while it is reviewed. You will be dmed in case of a decision.")

    @discord.app_commands.command()
    async def mobile_apply(self, interaction: discord.Interaction):
        """Apply for the verified role if on mobile with this command."""

        if self.client.server_info.VERIFIED_ROLE in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("You are already verified!", ephemeral=True)

        answers = []

        await interaction.response.send_message("Please check your dms", ephemeral=True)
        await interaction.user.send("Please answer the following questions. Optional questions will have an `(optional)` behind them, you can skip them if you want by typing something like - or N/A.")

        await sleep(1)

        for i in range(len(QUESTIONS)):
            try:
                await interaction.user.send(f"{QUESTIONS[i]['question']}" + (" (optional)" if not QUESTIONS[i]["required"] else ""))
                answer = await self.client.wait_for("message", timeout=100, check=lambda m: m.author == interaction.user and m.channel == interaction.user.dm_channel)
                while len(answer.content) >QUESTIONS[i]["max_length"]:
                    await interaction.user.send("❌ Answer too long. It can have a max of {} characters. Please try again.".format(QUESTIONS[i]["max_length"]))
                    answer = await self.client.wait_for("message", timeout=100, check=lambda m: m.author == interaction.user and m.channel == interaction.user.dm_channel)

                while "min_length" in QUESTIONS[i] and len(answer.content) < QUESTIONS[i]["min_length"]:
                    await interaction.user.send("❌ Answer too short. It must be at least {} characters. Please try again.".format(QUESTIONS[i]["min_length"]))
                    answer = await self.client.wait_for("message", timeout=100, check=lambda m: m.author == interaction.user and m.channel == interaction.user.dm_channel)

                answers.append(answer.content)
            except TimeoutError:
                return await interaction.user.send("❌ You took too long to answer. Application cancelled.")

        channel = self.client.get_channel(self.client.server_info.APPLICATION_CHANNEL)
        await channel.send(embed=self._to_embed(interaction.user, answers))
        await interaction.user.send("✅ Application submitted. Please be patient while it is reviewed. You will be dmed in case of a decision.")

    @discord.app_commands.command()
    @discord.app_commands.describe(member="The member to give the role to.")
    async def verify(self, interaction: discord.Interaction, member: discord.Member):
        """Grant a user the verified role."""
        if not self.client.server_info.WELCOMER_ROLE in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ You are not authorised to use this command!", ephemeral=True)

        if self.client.server_info.VERIFIED_ROLE not in [r.id for r in member.roles]:
            role = self.client.get_guild(self.client.server_info.ID).get_role(self.client.server_info.VERIFIED_ROLE)
            await member.add_roles(role)
            await interaction.response.send_message(f"✅ {member.mention} is now verified.", ephemeral=True)
            await member.send(f"Your application in Kids In The Dark has been reviewed and you have been granted access to the help channels!")
        else:
            await interaction.response.send_message(f"{member.mention} is already verified.")


Cog = Application

async def setup(client):
    await client.add_cog(Application(client))