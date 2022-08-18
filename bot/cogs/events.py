import discord

from discord.ext import commands, tasks

from bot.static.constants import DISBOARD, ACTIVITY_EVENT, EVENT
from bot.utils.classes import Member
from bot.utils.interactions import View, Button

from io import BytesIO
from typing import Dict
from random import randint, choices
from datetime import datetime, timedelta

class Events(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

        self.last_messages_cache: Dict[int, datetime] = {}

        self.water_banner_url = "https://cdn.discordapp.com/attachments/1004512555538067476/1008487607128301598/water.png"
        self.water_banner = None

        self.startup = datetime.now()

    @property
    def guild(self) -> discord.Guild:
        return self.client.get_guild(self.client.server_info.ID)

    @property
    def potato_channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.POTATO_BONUS_CHANNEL)

    @property
    def general_channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.GENERAL_CHANNEL)

    @property
    def sos_role(self) -> discord.Role:
        return self.guild.get_role(self.client.server_info.NEED_HELP_ROLE)

    async def cog_load(self):
        self.remove_sos_role.start()
        self.water.start()
        print("Loaded events cog")

    @tasks.loop(hours=2)
    async def water(self):
        """Sends a "drink water" reminder every 2 hours"""
        if not self.water_banner:
            res = await self.client.session.get(self.water_banner_url)
            image_bytes = await res.read()
            self.water_banner = image_bytes
            print(f"Successfully loaded water banner")

        if datetime.now() - self.startup < timedelta(minutes=5): # I don't want the banner to be sent when I start the bot
            return

        await self.general_channel.send(file=discord.File(filename="water.png", fp=BytesIO(self.water_banner)))

    @water.before_loop
    async def before_status(self):
        await self.client.wait_until_ready()

    @tasks.loop(hours=24)
    async def remove_sos_role(self):
        """Removes all help roles every 24 hours"""
        if datetime.now() - self.startup < timedelta(minutes=5): # I don't want the roles to be removed when I start the bot
            return

        for member in self.guild.members:
            if self.sos_role in member.roles:
                await member.remove_roles(self.sos_role)

    @remove_sos_role.before_loop
    async def before_remove_sos_role(self):
        await self.client.wait_until_ready()

    def handle_score(self, message: discord.Message):
        """Adds a calculated amount of points to the author of the message based on their activity"""
        if message.author.id in self.client.server_info.EVENT_EXCLUDED_MEMBERS or message.channel.id in self.client.server_info.EVENT_EXCLUDED_CHANNELS:
            return 

        base_points = 10
        member = Member(message.author.id)

        if str(message.channel.id) in member.last_messages and (datetime.now() - member.last_messages[str(message.channel.id)]) < timedelta(seconds=10):
            return # No added scores for spamming

        if message.channel.id in self.last_messages_cache and (datetime.now() - self.last_messages_cache[message.channel.id]) > timedelta(minutes=10): 
            base_points *= 2 # Double points for sending a message after a channel has been inactive for a while

        base_points *= 1 + 0.1 * member.streak # Increase points for streak

        base_points *= member.booster["times"] if member.booster else 1 # Multiply points by booster multiplier if booster is active

        base_points *= 1.2 if self.guild.get_member(member.id).premium_since else 1 # Give server booster a 1.2x bonus

        base_points *= member.diminishing_returns # Decrease points for diminishing returns

        base_points = round(base_points, 1) # Round to 1 decimal place

        member.add_message(message)
        member.add_points(base_points)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if ACTIVITY_EVENT and not message.author.bot:
            self.handle_score(message)

            self.last_messages_cache[message.channel.id] = datetime.now()

            if message.channel.id in self.client.server_info.EVENT_DROP_CHANNELS and randint(1, 10000) == 1: # 0.01% Chance of booster dropping
                booster = choices([2, 3, 4], weights=[0.6, 0.3, 0.1], k=1)[0] # Choose a random booster
                view = View()
                button = Button(label="Claim", style=discord.ButtonStyle.green)
                view.add_item(button)
                embed = discord.Embed(title="Booster dropped!", description=f"A `x{booster}` points booster has been dropped! Quick, claim it!".format(booster), color=0x2f3136)

                msg = await message.channel.send(embed=embed, view=view)
                await view.wait()

                if not view.timed_out:
                    winner = view.interaction.user
                    member = Member(winner.id)
                    member.add_booster(booster)
                    await view.interaction.response.send_message(f"{winner.mention} claimed the booster! Congrats! For the next hour, you will receive `x{booster}` points!")

                await view.disable(msg)

        if message.author.id != DISBOARD:
            return

        if len(message.embeds) > 0 and ":thumbsup:" in message.embeds[0].description:
            await self.potato_channel.send(f"{message.interaction.user.mention} has bumped the server! They have been awarded a bonus of 2🥔")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.client._change_presence()
        if ACTIVITY_EVENT and not member.bot and EVENT.find_one({ "_id": member.id }):
            EVENT.delete_one({ "_id": member.id })

Cog = Events