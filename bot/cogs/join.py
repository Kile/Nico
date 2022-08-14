import discord

from discord.ext import commands
from random import sample

from bot.utils.interactions import Modal
from bot.static.constants import WELCOME_MESSAGE, SERVER_QUESTIONS

class JoinModal(Modal):

    def __init__(self, user_id: int):
        super().__init__(user_id, title="Join questions")

        # Get a list of 3 random items from SERVER_QUESTIONS, so the questions are different every time
        self.questions = sample(SERVER_QUESTIONS, 3)

        for question in self.questions:
            self.add_item(discord.ui.TextInput(label=question["question"], required=True, style=discord.TextStyle.short))

class Join(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    async def cog_load(self):
        print("Loaded join cog")

    @property
    def guild(self) -> discord.Guild:
        return self.client.get_guild(self.client.server_info.ID)

    @property
    def welcome_channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.WELCOME_CHANNEL)

    @property
    def new_role(self) -> discord.Role:
        return self.guild.get_role(self.client.server_info.NEW_ROLE)

    @property
    def general_channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.GENERAL_CHANNEL)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != self.client.server_info.ID: return # Don't want that process when someone is joining on another server

        await self.client._change_presence()
        if member.bot: return

        await member.add_roles(self.new_role)

        embed = discord.Embed.from_dict({
            "title": "Welcome to the server!",
            "description": WELCOME_MESSAGE.format(member.display_name),
            "color": 0x2f3136,
            "footer": {
                "text": "Joined at " + member.joined_at.strftime("%H:%M:%S on %d/%m/%Y")
            }
        })
        await self.welcome_channel.send(content=member.mention, embed=embed)

    @discord.app_commands.command()
    async def join(self, interaction: discord.Interaction):
        """Answer a few questions to gain access to Kids In The Dark"""

        if interaction.guild:
            return await interaction.response.send_message("You can't use this command in a server", ephemeral=True)

        member = self.guild.get_member(interaction.user.id)

        if not member:
            return await interaction.response.send_message("You are not a member of the server this bot is made for so you cannot use this command.", ephemeral=True)

        if not self.new_role in member.roles:
            return await interaction.response.send_message("You already have access to the server!", ephemeral=True)

        modal = JoinModal(interaction.user.id)

        await interaction.response.send_modal(modal)

        await modal.wait()

        if modal.timed_out:
            return

        incorrect = []

        for pos, val in enumerate(modal.values):
            if not val.lower() in modal.questions[pos]["answer"]:
                incorrect.append(pos+1)
                
        if len(incorrect) > 0:
            text = (incorrect[0] if len(incorrect) == 1 else (f"{incorrect[0]} and {incorrect[1]}" if len(incorrect) == 2 else f"{incorrect[0]}, {incorrect[1]} and {incorrect[2]}")) 
            return await modal.interaction.response.send_message(f"Sadly your answer{'s' if len(incorrect) > 1 else ''} to question{'s' if len(incorrect) > 1 else ''} {text} {'is' if len(incorrect) > 1 else 'are'} incorrect! Please try again.")

        await member.remove_roles(self.new_role)
        await modal.interaction.response.send_message("Congratulations! You have answered all questions correctly! You have been given access to the server!")
        await self.general_channel.send(f"{member.mention} has been granted full access to the server!")

Cog = Join