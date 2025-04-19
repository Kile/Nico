from ctypes.wintypes import POINT
import discord

from discord.ext import commands, tasks

from bot.__init__ import Bot
from bot.static.constants import DISBOARD, ACTIVITY_EVENT, EVENT, POTATO, IMAGE_QUESTION_REGEX
from bot.utils.classes import Member, PotatoMember, HelloAgain
from bot.utils.interactions import View, Button

from re import search, IGNORECASE
from typing import Dict
from random import randint, choices
from datetime import datetime, timedelta

class Events(commands.Cog):

    def __init__(self, client: Bot):
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

    @property
    def voted_role(self) -> discord.Role:
        return self.guild.get_role(self.client.server_info.VOTED_ROLE)

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.remove_sos_role.is_running():
            self.remove_sos_role.start()
        if not self.water.is_running():
            self.water.start()
        print("Logged in as {0.user}!".format(self.client))

    # @tasks.loop(hours=12)
    # async def hello_again(self):
    #     """Sends a reminder the server exists if the user has not interacted in it a week after joining"""
    #     hello_again_obj = HelloAgain()
    #     members = hello_again_obj.needs_hello_again()

    #     for member in members:
    #         m = self.guild.get_member(member)
    #         embed = discord.Embed.from_dict({
    #             "title": "Hello again!",
    #             "description": f"Hey {m.mention}, you haven't talked a lot since you joined in Nico's Safe Space! Don't be shy, we'd love to hear more from you! Say hi in <#{self.client.server_info.GENERAL_CHANNEL}>!",
    #             "color": 0x2f3136
    #         })
    #         try:
    #             await m.send(embed=embed)
    #         except discord.Forbidden: # dms closed
    #             pass

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
        # Find if an attachment named "water.png" has been sent within the last 20 messages
        async for message in self.general_channel.history(limit=20):
            if message.author == self.client.user:
                if message.content.startswith(self.water_banner_url):
                    return
            # if message.attachments and message.author == self.client.user:
            #     for attachment in message.attachments:
            #         if attachment.filename == "water.png":
            #             return
                        
        # await self.general_channel.send(file=discord.File(filename="water.png", fp=BytesIO(self.water_banner)))
        await self.general_channel.send(self.water_banner_url)

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

    async def handle_potato(self, message: discord.Message):
        """Drops a potato in the chat and adds it to the inventory of the first member to send a potato emoji"""
        await PotatoMember.potato.delete()
        PotatoMember.potato = None
        await message.delete()

        member = PotatoMember(message.author.id)
        poisonous = randint(1, 10_000) == 1 # 0.01 % chance of getting a poisonous potato

        if poisonous:
            lost = randint(5, 10)
            member.remove_potatoes(lost)
            embed = discord.Embed.from_dict({
                "title": f":skull: POISONOUS POTATO :skull:",
                "description": f"{message.author} tried to pick up a poisonous potato, poisoning {lost} potatoes in the process and now holds on to {member.potatoes} potato{'es' if member.potatoes != 1 else ''}",
            })
        else:
            member.add_potatoes(1)
            embed = discord.Embed.from_dict({
                "title": ":potato: potato claimed :potato:",
                "description": f"{message.author} has claimed a potato and now holds on to {member.potatoes} potato{'es' if member.potatoes != 1 else ''}",
            })

        embed.colour = 0x2f3136
        embed.set_thumbnail(url=message.author.display_avatar.url if message.author.display_avatar else None)
        await message.channel.send(embed=embed)

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

        base_points *= 1.2 if message.author.premium_since else 1 # Give server booster a 1.2x bonus

        base_points *= member.diminishing_returns # Decrease points for diminishing returns

        base_points = round(base_points, 1) # Round to 1 decimal place

        member.add_message(message)
        member.add_points(base_points)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild != self.guild: return
        if message.author.bot: return
        # HelloAgain().add_message(message.author.id)

        if search(IMAGE_QUESTION_REGEX, message.content, IGNORECASE):
            await message.channel.send(
                embed=discord.Embed(
                    title="Image question detected 👀",
                    description="Looks like you are asking on why you cannot send images! " + \
                        "You need to pass the first stage of verification to be able to send images in the server. " + \
                        "Find detailed information on how to do this in <#726053325623263293>!",
                    color=0x2f3136
                ),
                reference=message,
                mention_author=False
            )

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

        if randint(1, 200) == 1 and message.channel.id in self.client.server_info.EVENT_DROP_CHANNELS and not message.author.bot and not PotatoMember.potato: # 0.01% Chance of potato dropping
            PotatoMember.potato = await message.channel.send(":potato:")

        if PotatoMember.potato and message.content in [":potato:", "🥔", "\U0001f954"] and PotatoMember.potato.channel.id == message.channel.id and message.author.id != PotatoMember.potato.author.id:
            await self.handle_potato(message)

        if message.author.id != DISBOARD:
            return

        if len(message.embeds) > 0 and ":thumbsup:" in message.embeds[0].description:
            PotatoMember(message.interaction.user.id).add_potatoes(2)
            await self.potato_channel.send(f"{message.interaction.user.mention} has bumped the server! They have been awarded a bonus of 2🥔")

    # @commands.Cog.listener()
    # async def on_member_update(self, before: discord.Member, after: discord.Member):
    #     # TEMPORARILY DISABLED

    #     if after.guild != self.guild: return

    #     if before.roles != after.roles:
    #         if self.voted_role in after.roles and self.voted_role not in before.roles:
    #             PotatoMember(after.id).add_potatoes(2)
    #             await self.potato_channel.send(f"{after.mention} has bumped the server on https://discords.com/servers/kidsinthedark ! They have been awarded a bonus of 2🥔")

    # @commands.Cog.listener()
    # async def on_member_remove(self, member: discord.Member):
    #     # TEMPORARILY DISABLED

    #     if member.guild != self.guild: return
    #     HelloAgain().remove_user(member.id)

    #     if len(member.guild.members) % 20 == 0:
    #         await self.client._change_presence()
    #     if ACTIVITY_EVENT and not member.bot and EVENT.find_one({ "_id": member.id }):
    #         EVENT.delete_one({ "_id": member.id })
    #     POTATO.delete_one({ "_id": member.id })

Cog = Events