import discord

from discord.ext import commands
from random import sample

from bot.__init__ import Bot
from bot.utils.interactions import Modal, View, Button
from bot.static.constants import WELCOME_MESSAGE, SERVER_QUESTIONS

class JoinModal(Modal):

    def __init__(self, user_id: int):
        super().__init__(user_id, title="Join questions")

        # Get a list of 3 random items from SERVER_QUESTIONS, so the questions are different every time
        self.questions = sample(SERVER_QUESTIONS, 3)

        for question in self.questions:
            self.add_item(discord.ui.TextInput(label=question["question"], required=True, style=discord.TextStyle.short))

class WelcomeButton(Button):

    def __init__(self, message: discord.Message, joining: discord.Member):
        super().__init__(label="Welcome", emoji="<a:wave_animated:1013553177259430008>", style=discord.ButtonStyle.gray)
        self.message = message
        self.joining = joining
        self.welcomed = []
        self.emotes = ["<a:PikaWave:1013541266203623525>", "<a:RainbowHeart:1013541653056868383>", "<:ShibeHeart:1013541794199388210>", "<a:ablobwave:1013541120610930738>", "<:doggowave:1013541355978493962>", 
        "<:obamaheart:1013541594395316354>", "<a:wave_animated:1013553177259430008>", "<a:hyperwave:1013553221618376805>", "<:foxwave:1013553116760784936>", "<:cir_wave:1013553330024361986>"]

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id in [m for m, _ in self.welcomed]:
            return await interaction.response.send_message("You have already welcomed the new user!", ephemeral=True)
        if interaction.user.id == self.joining.id:
            return await interaction.response.send_message("You can't welcome yourself!", ephemeral=True)

        view = View(interaction.user.id, timeout=30)
        for emote in self.emotes:
            view.add_item(Button(emoji=emote, style=discord.ButtonStyle.gray, custom_id=emote))

        await interaction.response.send_message("Please chose what emoji to welcome them with!", view=view, ephemeral=True)

        await view.wait()

        if view.timed_out or not view.interaction:
            return await view.disable(await interaction.original_response())

        self.welcomed.append((interaction.user.id, view.value))

        self.message.embeds[0].description = WELCOME_MESSAGE.format(self.joining.name) + "\n**༺♥️༻ㆍ You were welcomed by:**\n> " + "\n> ".join([f"{self.message.guild.get_member(id).name}*#{self.message.guild.get_member(id).discriminator}* {emote}" for id, emote in self.welcomed]) + "\n\nI hope you enjoy your stay!"

        await self.message.edit(embed=self.message.embeds[0])
        await view.interaction.response.send_message(":thumbsup: You have welcomed the new user!", ephemeral=True)
        await view.disable(await interaction.original_response())

class Join(commands.Cog):

    def __init__(self, client: Bot):
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
            "description": WELCOME_MESSAGE.format(member.display_name) + "\n\nI hope you enjoy your stay!",
            "color": 0x2f3136,
            "footer": {
                "text": "Joined at " + member.joined_at.strftime("%H:%M:%S on %d/%m/%Y")
            }
        })
        message = await self.welcome_channel.send(content=member.mention, embed=embed)

        view = View(timeout=600)
        view.add_item(WelcomeButton(message, member))

        notification = await self.general_channel.send(f"<:member_join:1013795687508484116> **{member}** just joined! They cannot see this channel yet, instead press the welcome button to welcome them!", view=view)

        await view.wait()

        await view.disable(notification)

    @discord.app_commands.command()
    async def join(self, interaction: discord.Interaction):
        """Answer a few questions to gain access to Nico's Safe Space"""

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