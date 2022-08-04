import discord
from discord.ext import commands

from typing import Union
from asyncio import sleep, TimeoutError

from bot.utils.interactions import Modal, View, Button

class ApplicationModal(Modal):

    def __init__(self, user_id: int, page: int):
        super().__init__(user_id, title="Application")
        if page == 1:
            self.add_item(discord.ui.TextInput(label="Have you read the welcome message and rules?", placeholder="Yes/No/Maybe", max_length=100))
            self.add_item(discord.ui.TextInput(label="Where did you find the link to join?", placeholder="Disboard/Google/YT/etc", max_length=100))
            self.add_item(discord.ui.TextInput(label="How old are you?", placeholder="13-21", required=False, max_length=50))
            self.add_item(discord.ui.TextInput(label="What are your preferred pronouns?", placeholder="He/She/They", required=False, max_length=50))
            self.add_item(discord.ui.TextInput(label="What is your sex?", placeholder="male/female", required=False, max_length=50))
        elif page == 2:
            self.add_item(discord.ui.TextInput(label="Where are you from?", placeholder="America/UK/Germany...", required=False, max_length=200))
            self.add_item(discord.ui.TextInput(label="Are you suicidal or self harm?", placeholder="I self harm/I am suicidal/neither/both", max_length=200))
            self.add_item(discord.ui.TextInput(label="Are you easily triggered?", placeholder="Yes/No", max_length=100))
            self.add_item(discord.ui.TextInput(label="Why do you want access to the help channels?", placeholder="Because...", max_length=200))
            self.add_item(discord.ui.TextInput(label="Do you suffer from any disorders?", placeholder="Yes I have.../No", required=False, max_length=200))
        else:
            self.add_item(discord.ui.TextInput(label="Do you have experience helping others?", placeholder="Yes/No", max_length=200))
            self.add_item(discord.ui.TextInput(label="Tell us a bit about yourself", placeholder="I like cookies", max_length=200, style=discord.TextStyle.long, min_length=50))

class Application(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def cog_load(self):
        print("Loaded")

    def _to_embed(self, user: Union[discord.Member, discord.User], responses: list) -> discord.Embed:
        embed = discord.Embed.from_dict({
            "title": f"Application of {user.name}",
            "description": user.mention,
            "fields": [
                {"name": "Have you read the welcome message and rules?", "value": responses[0]},
                {"name": "Where did you find the link to join?", "value": responses[1]},
                {"name": "How old are you?", "value": responses[2] or "N/A"},
                {"name": "What are your preffered pronouns?", "value": responses[3] or "N/A"},
                {"name": "What is your sex?", "value": responses[4] or "N/A"},
                {"name": "Where are you from?", "value": responses[5] or "N/A"},
                {"name": "Are you suicidal or self harm?", "value": responses[6]},
                {"name": "Are you easily triggered?", "value": responses[7]},
                {"name": "Why do you want access to the help channels?", "value": responses[8]},
                {"name": "Do you suffer from any disorders?", "value": responses[9] or "N/A"},
                {"name": "Do you have experience helping others?", "value": responses[10]},
                {"name": "Tell us a bit about yourself", "value": responses[11]}
            ],
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

        questions = [
            {
                "question": "Have you read the welcome message and rules?",
                "required": True,
                "max_length": 100
            },
            {
                "question": "Where did you find the link to join?",
                "required": True,
                "max_length": 100
            },
            {
                "question": "How old are you?",
                "required": False,
                "max_length": 50
            },
            {
                "question": "What are your preferred pronouns?",
                "required": False,
                "max_length": 50
            },
            {
                "question": "What is your sex?",
                "required": False,
                "max_length": 50
            },
            {
                "question": "Where are you from?",
                "required": True,
                "max_length": 200
            },
            {
                "question": "Are you suicidal or self harm?",
                "required": True,
                "max_length": 100
            },
            {
                "question": "Are you easily triggered?",
                "required": True,
                "max_length": 50
            },
            {
                "question": "Why do you want access to the help channels?",
                "required": True,
                "max_length": 200
            },
            {
                "question": "Do you suffer from any disorders?",
                "required": False,
                "max_length": 200
            },
            {
                "question": "Do you have experience helping others?",
                "required": True,
                "max_length": 100
            },
            {
                "question": "Tell us a bit about yourself.",
                "required": True,
                "max_length": 200,
                "min_length": 50
            }
        ]

        answers = []

        await interaction.response.send_message("Please check your dms", ephemeral=True)
        await interaction.user.send("Please answer the following questions. Optional questions will have an `(optional)` behind them, you can skip them if you want by typing something like - or N/A.")

        await sleep(1)

        for i in range(len(questions)):
            print(i)
            try:
                await interaction.user.send(f"{questions[i]['question']}" + (" (optional)" if not questions[i]["required"] else ""))
                answer = await self.client.wait_for("message", timeout=100, check=lambda m: m.author == interaction.user and m.channel == interaction.user.dm_channel)
                while len(answer.content) > questions[i]["max_length"]:
                    await interaction.user.send("❌ Answer too long. It can have a max of {} characters. Please try again.".format(questions[i]["max_length"]))
                    answer = await self.client.wait_for("message", timeout=100, check=lambda m: m.author == interaction.user and m.channel == interaction.user.dm_channel)

                while "min_length" in questions[i] and len(answer.content) < questions[i]["min_length"]:
                    await interaction.user.send("❌ Answer too short. It must be at least {} characters. Please try again.".format(questions[i]["min_length"]))
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