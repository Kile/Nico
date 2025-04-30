from ctypes.wintypes import POINT
import discord

from discord.ext import commands, tasks
from discord.ui import View, Button

from bot.__init__ import Bot
from bot.static.constants import (
    DISBOARD,
    ACTIVITY_EVENT,
    EVENT,
    TRANSLATE_EMOJI,
    IMAGE_QUESTION_REGEX,
    CONSTANTS,
    TAG_QUESTION_REGEX,
    TAG_INTERACTIONAL_REGEX,
    KILLUA_BOOSTER_ROLE,
    KILLUA_SERVER,
    WHO_PINGED_ME_REGEX,
)
from bot.utils.classes import Member, PotatoMember, HelloAgain
from bot.utils.interactions import View, Button

from re import search, IGNORECASE, sub, escape
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
    def killua_guild(self) -> discord.Guild:
        return self.client.get_guild(KILLUA_SERVER)

    @property
    def killua_booster_role(self) -> discord.Role:
        return self.killua_guild.get_role(KILLUA_BOOSTER_ROLE)

    @property
    def killua_booster_role_nss(self) -> discord.Role:
        return self.guild.get_role(self.client.server_info.KILLUA_BOOSTER_ROLE)

    @property
    def booster_channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.BOOSTER_CHANNEL)

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

    @property
    def new_role(self) -> discord.Role:
        return self.guild.get_role(self.client.server_info.NEW_ROLE)

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.remove_sos_role.is_running():
            self.remove_sos_role.start()
        if not self.water.is_running():
            self.water.start()
        if not self.add_killua_booster_role.is_running():
            self.add_killua_booster_role.start()
        print("Logged in as {0.user}!".format(self.client))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if reaction.message.guild != self.guild:
            return
        if not (self.new_role in self.guild.get_member(user.id).roles):
            return
        # if the reaction is named middle_finger or is a middle finger, kick person and remove the reaction (unless its the first)
        if reaction.emoji == "\U0001f595" or (
            hasattr(reaction.emoji, "name")
            and (
                "middle_finger" in reaction.emoji.name.lower()
                or "fuck" in reaction.emoji.name.lower()
            )
        ):
            member = self.guild.get_member(user.id)
            if not member:
                return
            await member.kick(reason="Naughty reaction :)")
            if reaction.count > 1:
                await reaction.remove(user)

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

        if datetime.now() - self.startup < timedelta(
            minutes=5
        ):  # I don't want the banner to be sent when I start the bot
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
        if datetime.now() - self.startup < timedelta(
            minutes=5
        ):  # I don't want the roles to be removed when I start the bot
            return

        for member in self.guild.members:
            if self.sos_role in member.roles:
                await member.remove_roles(self.sos_role)

    @remove_sos_role.before_loop
    async def before_remove_sos_role(self):
        await self.client.wait_until_ready()

    @tasks.loop(minutes=2)
    async def add_killua_booster_role(self):
        """Add the "Killua booster" role to all member who are a booster on the KILLUA_SERVER"""
        if datetime.now() - self.startup < timedelta(minutes=1):
            return

        has_role_on_nss = [
            m for m in self.guild.members if self.killua_booster_role_nss in m.roles
        ]
        has_role_on_killua = [
            m for m in self.killua_guild.members if self.killua_booster_role in m.roles
        ]

        try:
            for member in has_role_on_killua:
                if member.id not in [m.id for m in has_role_on_nss]:
                    nss_member = self.guild.get_member(member.id)
                    if nss_member:
                        await nss_member.add_roles(self.killua_booster_role_nss)
                        await self.booster_channel.send(
                            f"{nss_member.mention} has been given the Killua booster role for being a booster on the Killua server! Thank you for your support!"
                        )

            # Other way around
            for member in has_role_on_nss:
                if member.id not in [m.id for m in has_role_on_killua]:
                    nss_member = self.guild.get_member(member.id)
                    if nss_member:
                        await nss_member.remove_roles(self.killua_booster_role_nss)
        except Exception as e:  # Dont want the task to stop if something goes wrong
            print("Exception in booster task: " + e)

    async def handle_potato(self, message: discord.Message):
        """Drops a potato in the chat and adds it to the inventory of the first member to send a potato emoji"""
        await PotatoMember.potato.delete()
        PotatoMember.potato = None
        await message.delete()

        member = PotatoMember(message.author.id)
        poisonous = (
            randint(1, 10_000) == 1
        )  # 0.01 % chance of getting a poisonous potato

        if poisonous:
            lost = randint(5, 10)
            member.remove_potatoes(lost)
            embed = discord.Embed.from_dict(
                {
                    "title": f":skull: POISONOUS POTATO :skull:",
                    "description": f"{message.author} tried to pick up a poisonous potato, poisoning {lost} potatoes in the process and now holds on to {member.potatoes} potato{'es' if member.potatoes != 1 else ''}",
                }
            )
        else:
            member.add_potatoes(1)
            embed = discord.Embed.from_dict(
                {
                    "title": ":potato: potato claimed :potato:",
                    "description": f"{message.author} has claimed a potato and now holds on to {member.potatoes} potato{'es' if member.potatoes != 1 else ''}",
                }
            )

        embed.colour = 0x2F3136
        embed.set_thumbnail(
            url=(
                message.author.display_avatar.url
                if message.author.display_avatar
                else None
            )
        )
        await message.channel.send(embed=embed)

    def handle_score(self, message: discord.Message):
        """Adds a calculated amount of points to the author of the message based on their activity"""
        if (
            message.author.id in self.client.server_info.EVENT_EXCLUDED_MEMBERS
            or message.channel.id in self.client.server_info.EVENT_EXCLUDED_CHANNELS
        ):
            return

        base_points = 10
        member = Member(message.author.id)

        if str(message.channel.id) in member.last_messages and (
            datetime.now() - member.last_messages[str(message.channel.id)]
        ) < timedelta(seconds=10):
            return  # No added scores for spamming

        if message.channel.id in self.last_messages_cache and (
            datetime.now() - self.last_messages_cache[message.channel.id]
        ) > timedelta(minutes=10):
            base_points *= 2  # Double points for sending a message after a channel has been inactive for a while

        base_points *= 1 + 0.1 * member.streak  # Increase points for streak

        base_points *= (
            member.booster["times"] if member.booster else 1
        )  # Multiply points by booster multiplier if booster is active

        base_points *= (
            1.2 if message.author.premium_since else 1
        )  # Give server booster a 1.2x bonus

        base_points *= (
            member.diminishing_returns
        )  # Decrease points for diminishing returns

        base_points = round(base_points, 1)  # Round to 1 decimal place

        member.add_message(message)
        member.add_points(base_points)

    async def verify_callback(self, interaction: discord.Interaction):
        """Callback for the verify button"""
        applicant = interaction.guild.get_member(
            int(interaction.data["custom_id"].split(":")[1])
        )

        role = interaction.guild.get_role(self.client.server_info.VERIFIED_ROLE)
        # Workaround for not being able to access wether it is a testing evironment or not

        await applicant.add_roles(role)
        await interaction.response.send_message(
            f"✅ Verified {applicant.mention}", ephemeral=True
        )
        try:
            await applicant.send(
                f"Your application in Nico's Safe Space has been approved and you can now pick up roles (with `/roles help`) to access sensitive channels! "
            )
        except discord.HTTPException:
            pass  # Ignore closed dms

        # Edit the buttons
        verified_button = Button(
            style=discord.ButtonStyle.green,
            label=f"Verified by {interaction.user}",
            disabled=True,
        )
        view = View()
        view.add_item(verified_button)

        await interaction.message.edit(view=view)

    async def deny_callback(self, interaction: discord.Interaction):
        applicant = interaction.guild.get_member(
            int(interaction.data["custom_id"].split(":")[1])
        )

        # save applicant id to denied database
        existing = CONSTANTS.find_one({"_id": "denied"})

        if not existing:
            CONSTANTS.insert_one({"_id": "denied", "ids": [applicant.id]})
        else:
            CONSTANTS.update_one({"_id": "denied"}, {"$push": {"ids": applicant.id}})

        await interaction.response.send_message(
            f"✅ Denied {applicant.mention}", ephemeral=True
        )

        try:
            await applicant.send(
                f"Your application in Nico's Safe Space has been denied. If you think this is a mistake, please contact a staff member."
            )
        except discord.HTTPException:
            pass

        # Edit the buttons
        denied_button = Button(
            style=discord.ButtonStyle.grey,
            label=f"Denied by {interaction.user}",
            disabled=True,
        )
        view = View()
        view.add_item(denied_button)

        await interaction.message.edit(view=view)

    async def un_timeout(self, interaction: discord.Interaction):
        """Callback for the un_timeout button"""
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message(
                "You don't have the permissions to do that!", ephemeral=True
            )
        member = self.guild.get_member(int(interaction.data["custom_id"].split(":")[1]))
        if not member:
            return await interaction.response.send_message(
                "Member not found", ephemeral=True
            )
        if member.timed_out_until:
            await member.timeout(None, reason="Un-timeout by moderator")
            await interaction.response.send_message(
                f"✅ Un-timed out {member.mention}", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Member is not timed out", ephemeral=True
            )
        view = (
            View()
            .add_item(
                Button(
                    label="Removed timeout",
                    style=discord.ButtonStyle.green,
                    disabled=True,
                )
            )
            .add_item(
                Button(
                    label="Mod: " + interaction.user.display_name,
                    style=discord.ButtonStyle.grey,
                    disabled=True,
                )
            )
        )
        await interaction.message.edit(view=view)

    async def kick(self, interaction: discord.Interaction):
        """Callback for the kick button"""
        if not interaction.user.guild_permissions.kick_members:
            return await interaction.response.send_message(
                "You don't have the permissions to do that!", ephemeral=True
            )
        member = self.guild.get_member(int(interaction.data["custom_id"].split(":")[1]))
        if not member:
            return await interaction.response.send_message(
                "Member not found", ephemeral=True
            )
        try:
            await member.kick(reason="Kicked by moderator")
            await interaction.response.send_message(
                f"✅ Kicked {member.mention}", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have the permissions to do that!", ephemeral=True
            )
        view = (
            View()
            .add_item(
                Button(label="Kicked", style=discord.ButtonStyle.red, disabled=True)
            )
            .add_item(
                Button(
                    label="Mod: " + interaction.user.display_name,
                    style=discord.ButtonStyle.grey,
                    disabled=True,
                )
            )
        )
        await interaction.message.edit(view=view)

    async def ban(self, interaction: discord.Interaction):
        """Callback for the ban button"""
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message(
                "You don't have the permissions to do that!", ephemeral=True
            )
        member = self.guild.get_member(int(interaction.data["custom_id"].split(":")[1]))
        if not member:
            return await interaction.response.send_message(
                "Member not found", ephemeral=True
            )
        try:
            await member.ban(reason="Banned by moderator")
            await interaction.response.send_message(
                f"✅ Banned {member.mention}", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have the permissions to do that!", ephemeral=True
            )
        view = (
            View()
            .add_item(
                Button(label="Banned", style=discord.ButtonStyle.red, disabled=True)
            )
            .add_item(
                Button(
                    label="Mod: " + interaction.user.display_name,
                    style=discord.ButtonStyle.grey,
                    disabled=True,
                )
            )
        )
        await interaction.message.edit(view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.data.get("custom_id", False):
            return
        if interaction.guild != self.guild and not interaction.data[
            "custom_id"
        ].startswith("translate"):
            return
        if interaction.user.bot:
            return

        if interaction.data["custom_id"].startswith("verify"):
            await self.verify_callback(interaction)
        elif interaction.data["custom_id"].startswith("deny"):
            await self.deny_callback(interaction)
        elif interaction.data["custom_id"].startswith("translate"):
            return await self.client.translate_callback(interaction)
        elif interaction.data["custom_id"].startswith("un_timeout"):
            await self.un_timeout(interaction)
        elif interaction.data["custom_id"].startswith("kick"):
            await self.kick(interaction)
        elif interaction.data["custom_id"].startswith("ban"):
            await self.ban(interaction)
        elif interaction.data["custom_id"].startswith("revive_remove"):
            _id = int(interaction.data["custom_id"].split(":")[1])
            if interaction.user.id != _id:
                return await interaction.response.send_message(
                    "You can't use this button to remove your own role.", ephemeral=True
                )
            await interaction.user.remove_roles(
                interaction.guild.get_role(self.client.server_info.CHAT_REVIVE_ROLE)
            )
            await interaction.response.send_message(
                "Your chat revive role has been removed!", ephemeral=True
            )
            await interaction.message.edit(
                view=View().add_item(
                    Button(
                        label="Role Removed",
                        style=discord.ButtonStyle.green,
                        disabled=True,
                    )
                )
            )
        elif interaction.data["custom_id"].startswith("dismiss"):
            _id = int(interaction.data["custom_id"].split(":")[1])
            if interaction.user.id != _id:
                return await interaction.response.send_message(
                    "You can't use this button.", ephemeral=True
                )
            await interaction.response.defer()
            await interaction.message.delete()

    def highlight_question_and_keyword(sekf, text: str):
        match_question = search(TAG_QUESTION_REGEX, text, IGNORECASE)
        if match_question:
            question_word = match_question.group(1)
            keyword = match_question.group(2)
            highlighted_text = sub(
                r"\b" + escape(question_word) + r"\b",
                f"**__{question_word}__**",
                text,
                flags=IGNORECASE,
            )
            highlighted_text = sub(
                r"\b" + escape(keyword) + r"\b",
                f"**__{keyword}__**",
                highlighted_text,
                flags=IGNORECASE,
            )
            return highlighted_text, [question_word, keyword]

        match_interactional = search(TAG_INTERACTIONAL_REGEX, text, IGNORECASE)
        if match_interactional:
            keyword = match_interactional.group(2)
            highlighted_text = sub(
                r"\b" + escape(keyword) + r"\b",
                f"**__{keyword}__**",
                text,
                flags=IGNORECASE,
            )
            # We don't have an explicit question word in this regex to highlight
            return highlighted_text, [keyword]

    async def tag_question_core(self, message: discord.Message, certain: bool = False):
        """Handles the tag question"""
        if not self.new_role in message.author.roles:
            return

        # Delete message and timeout user
        await message.delete()
        try:
            await message.author.timeout(
                discord.utils.utcnow() + timedelta(days=1), reason="Asked about tag"
            )
            # Add joined for tag role
            role = self.guild.get_role(self.client.server_info.JOINED_FOR_TAG_ROLE)
            await message.author.add_roles(role)
        except discord.Forbidden:
            pass

        # Dm the user about why they were timed out
        embed = discord.Embed(
            title="Timed out for mentioning tags",
            description="You were muted for asking about tags."
            + "\nTo use our VIP tag you do not need to have full access to the server."
            + "\nYou can get the tag by going to Settings > User Profile > Tags and selecting the tag you want."
            + "\nIf you want to actually participate in the server, you can click the button to come back when your timeout ends.",
        )
        embed.set_image(
            url="https://media.discordapp.net/attachments/1004512555538067476/1365081861038145546/tag.gif?ex=680c030d&is=680ab18d&hm=b68d21244a251c7bf4b6dfc1e78ee8b433231f4a3bbb8c1851cf50c6b154cc3d&=&width=2226&height=1420"
        )
        view = View()
        translate_button = Button(
            label="Translate",
            style=discord.ButtonStyle.blurple,
            custom_id=f"translate:tag_check",
            emoji=TRANSLATE_EMOJI,
        )
        view.add_item(translate_button)
        could_dm = True
        try:
            await message.author.send(embed=embed, view=view)
        except discord.HTTPException:
            could_dm = False

        text_with_matches_highlighted, keywords = self.highlight_question_and_keyword(
            message.content
        )

        mod_message = discord.Embed(
            title="Tag question detected",
            description=message.author.mention
            + " in "
            + message.channel.mention
            + ":\n> "
            + text_with_matches_highlighted
            + "\n\n"
            + "Keywords triggered: "
            + ", ".join(keywords)
            + ("\n\U000026a0 **Failed to dm user**" if not could_dm else ""),
            color=0x2F3136,
        )
        mod_message.set_author(
            name=message.author.display_name, icon_url=message.author.display_avatar.url
        )
        mod_message.set_footer(
            text=f"User ID: {message.author.id} | Certainty: {'high' if certain else 'low'}"
        )
        view = View()
        un_timeout_button = Button(
            label="Remove timeout",
            style=discord.ButtonStyle.green,
            custom_id=f"un_timeout:{message.author.id}",
        )
        kick_button = Button(
            label="Kick",
            style=discord.ButtonStyle.red,
            custom_id=f"kick:{message.author.id}",
        )
        ban_button = Button(
            label="Ban",
            style=discord.ButtonStyle.red,
            custom_id=f"ban:{message.author.id}",
        )
        view.add_item(un_timeout_button).add_item(kick_button).add_item(ban_button)
        await self.client.get_channel(self.client.server_info.MOD_CHANNEL).send(
            embed=mod_message, view=view
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild != self.guild:
            return
        if message.author.bot:
            return
        # HelloAgain().add_message(message.author.id)

        if search(IMAGE_QUESTION_REGEX, message.content, IGNORECASE):
            await message.channel.send(
                embed=discord.Embed(
                    title="Image question detected 👀",
                    description="Looks like you are asking on why you cannot send images! "
                    + "You need to pass the first stage of verification to be able to send images in the server. "
                    + "Find detailed information on how to do this in <#726053325623263293>!",
                    color=0x2F3136,
                ),
                reference=message,
                mention_author=False,
            )

        if search(
            WHO_PINGED_ME_REGEX, message.content, IGNORECASE
        ) and self.client.server_info.CHAT_REVIVE_ROLE in [
            r.id for r in message.author.roles
        ]:
            await message.channel.send(
                embed=discord.Embed(
                    title="Who pinged me?",
                    description="Looks like you are asking who pinged you! "
                    + f"You have the <@&{self.client.server_info.CHAT_REVIVE_ROLE}> role, which is pinged occasionally to revive the chat. "
                    + "If you don't want to be pinged for this anymore, you can remove the chat revive role through this button.",
                    color=0x2F3136,
                ),
                reference=message,
                mention_author=False,
                view=View()
                .add_item(
                    Button(
                        label="Remove chat revive role",
                        style=discord.ButtonStyle.blurple,
                        custom_id=f"revive_remove:" + str(message.author.id),
                    )
                )
                .add_item(
                    Button(
                        label="False flag/Dismiss",
                        style=discord.ButtonStyle.red,
                        custom_id=f"dismiss:" + str(message.author.id),
                    )
                ),
            )

        if search(TAG_QUESTION_REGEX, message.content, IGNORECASE):
            await self.tag_question_core(message, True)
        elif search(TAG_INTERACTIONAL_REGEX, message.content, IGNORECASE):
            await self.tag_question_core(message, False)

        if ACTIVITY_EVENT and not message.author.bot:
            self.handle_score(message)

            self.last_messages_cache[message.channel.id] = datetime.now()

            if (
                message.channel.id in self.client.server_info.EVENT_DROP_CHANNELS
                and randint(1, 10000) == 1
            ):  # 0.01% Chance of booster dropping
                booster = choices([2, 3, 4], weights=[0.6, 0.3, 0.1], k=1)[
                    0
                ]  # Choose a random booster
                view = View()
                button = Button(label="Claim", style=discord.ButtonStyle.green)
                view.add_item(button)
                embed = discord.Embed(
                    title="Booster dropped!",
                    description=f"A `x{booster}` points booster has been dropped! Quick, claim it!".format(
                        booster
                    ),
                    color=0x2F3136,
                )

                msg = await message.channel.send(embed=embed, view=view)
                await view.wait()

                if not view.timed_out:
                    winner = view.interaction.user
                    member = Member(winner.id)
                    member.add_booster(booster)
                    await view.interaction.response.send_message(
                        f"{winner.mention} claimed the booster! Congrats! For the next hour, you will receive `x{booster}` points!"
                    )

                await view.disable(msg)

        if (
            randint(1, 200) == 1
            and message.channel.id in self.client.server_info.EVENT_DROP_CHANNELS
            and not message.author.bot
            and not PotatoMember.potato
        ):  # 0.5% Chance of potato dropping
            PotatoMember.potato = await message.channel.send(":potato:")

        if (
            PotatoMember.potato
            and message.content in [":potato:", "🥔", "\U0001f954"]
            and PotatoMember.potato.channel.id == message.channel.id
            and message.author.id != PotatoMember.potato.author.id
        ):
            await self.handle_potato(message)

        if message.author.id != DISBOARD:
            return

        if len(message.embeds) > 0 and ":thumbsup:" in message.embeds[0].description:
            PotatoMember(message.interaction.user.id).add_potatoes(2)
            await self.potato_channel.send(
                f"{message.interaction.user.mention} has bumped the server! They have been awarded a bonus of 2🥔"
            )

    # @commands.Cog.listener()
    # async def on_member_update(self, before: discord.Member, after: discord.Member):
    #     if after.guild != self.guild: return

    #     if before.roles != after.roles:
    #         if self.voted_role in after.roles and self.voted_role not in before.roles:
    #             PotatoMember(after.id).add_potatoes(2)
    #             await self.potato_channel.send(f"{after.mention} has bumped the server on https://discords.com/servers/kidsinthedark ! They have been awarded a bonus of 2🥔")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # TEMPORARILY DISABLED

        if member.guild != self.guild:
            return
        # HelloAgain().remove_user(member.id)

        if len(member.guild.members) % 250 == 0:
            await self.client._change_presence()
        if ACTIVITY_EVENT and not member.bot and EVENT.find_one({"_id": member.id}):
            EVENT.delete_one({"_id": member.id})
        # POTATO.delete_one({ "_id": member.id })


Cog = Events
