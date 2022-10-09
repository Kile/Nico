import discord

from discord.ext import commands

import inspect, os
from typing import Optional
from datetime import datetime, timedelta

from bot.__init__ import Bot
from bot.static.constants import GUILD_OBJECT, DID_INFO, CONSTANTS

class Url(discord.ui.View):
    def __init__(self, url: str, label: str = 'Open', emoji: Optional[str] = None):
        super().__init__()
        self.add_item(discord.ui.Button(label=label, emoji=emoji, url=url))

class Various(commands.Cog):

    def __init__(self, client: Bot):
        self.client = client

    async def cog_load(self):
        print("Loaded various cog")

    @property
    def guild(self) -> discord.Guild:
        return self.client.get_guild(self.client.server_info.ID)

    @property
    def chat_revive(self) -> discord.Role:
        return self.guild.get_role(self.client.server_info.CHAT_REVIVE_ROLE)

    @discord.app_commands.command()
    @discord.app_commands.guilds(GUILD_OBJECT)
    async def did(self, interaction: discord.Interaction):
        """Gives you an explenation of did, short for Dissociative Identity Disorder"""

        embed = discord.Embed.from_dict({
            "title": "What is DID?",
            "description": DID_INFO,
            "color": 0x2f3136
        })

        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command()
    @discord.app_commands.guilds(GUILD_OBJECT)
    async def revive(self, interaction: discord.Interaction):
        """Pings the "chat revive" role. Only usable every 2 hours by a member with the verified role."""

        if not self.client.server_info.VERIFIED_ROLE in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("You are not verified! Get verified with `/apply`", ephemeral=True)

        if interaction.channel.id != self.client.server_info.GENERAL_CHANNEL:
            return await interaction.response.send_message(f"You can only use this command in <#{self.client.server_info.GENERAL_CHANNEL}>", ephemeral=True)

        data = CONSTANTS.find_one({"_id": "chat_revive"})

        if data and (datetime.now() - data["last_ping"]) < timedelta(hours=2):
            return await interaction.response.send_message(f"You can only ping the chat revive role every 2 hours. You can next ping it <t:{int((data['last_ping'] + timedelta(hours=2)).timestamp())}:R>", ephemeral=True)

        counter = 0
        messangers = []

        async for message in interaction.channel.history(limit=10, after=datetime.now() - timedelta(minutes=2)):
            counter += 1
            if message.author.id not in messangers:
                messangers.append(message.author.id)

        if counter == 10 and len(messangers) > 2:
            return await interaction.response.send_message(f"The chat is currently too active to ping the chat revive role!", ephemeral=True)

        if data:
            CONSTANTS.update_one({"_id": "chat_revive"}, {"$set": {"last_ping": datetime.now(), "last_ping_by": interaction.user.id}})
        else:
            CONSTANTS.insert_one({"_id": "chat_revive", "last_ping": datetime.now(), "last_ping_by": interaction.user.id})
        await interaction.response.send_message(f"{interaction.user.mention} calls upon the mighty {self.chat_revive.mention}!", allowed_mentions=discord.AllowedMentions.all())

    @discord.app_commands.command()
    @discord.app_commands.guilds(GUILD_OBJECT)
    async def close(self, interaction: discord.Interaction, reason: str = None):
        """Closes the current help thread"""

        if not isinstance(interaction.channel, discord.Thread):
            return await interaction.response.send_message("This command can only be used in a forum thread", ephemeral=True)

        if not isinstance(interaction.channel.parent, discord.ForumChannel):
            return await interaction.response.send_message("This command can only be used in a forum thread", ephemeral=True)

        # Check if the channel is already closed
        if interaction.channel.archived:
            return await interaction.response.send_message("This thread is already closed!", ephemeral=True)

        try:
            original_message = await interaction.channel.fetch_message(interaction.channel.id)
        except discord.NotFound:
            pass # This only means the author of the post now cannot delete it

        if not (((original_message and interaction.user in original_message.mentions) and interaction.channel_id == self.client.server_info.SOS_CHANNEL) or \
            interaction.channel.owner) and not self.client.server_info.WILL_HELP_ROLE in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(f"You can only use this thread if you have the <@&{self.client.server_info.WILL_HELP_ROLE}> role or are the thread creator.", ephemeral=True)

        await interaction.response.send_message(f"{interaction.user.mention} has closed this post{' with the reason: ' + reason if reason else '.'}", allowed_mentions=discord.AllowedMentions.all())
        await interaction.channel.edit(archived=True, locked=True if self.client.server_info.TRUSTED_ROLE else False)

    @discord.app_commands.command()
    @discord.app_commands.guilds(GUILD_OBJECT)
    @discord.app_commands.describe(command="The command to see the source code of")
    async def source(self, interaction: discord.Interaction, command: str = None):
        """
        Links to the bots code, or a specific command's
        """
        # This command was taken and modified from
        # https://github.com/LeoCx1000/discord-bots/blob/master/DuckBot/cogs/info.py

        global obj
        source_url = "https://github.com/Kile/Nico"
        branch = "master"
        license_url = f"{source_url}/blob/master/LICENSE"
        mpl_advice = (
            f"**This code is licensed under [MPL]({license_url})**"
            f"\nRemember that you must use the "
            f"\nsame license! [[read more]]({license_url}#L160-L168)"
        )
        obj = None

        if command is None:
            embed = discord.Embed(title=f"Here's my source code.", description=mpl_advice)
            embed.set_image(url="https://cdn.discordapp.com/attachments/879251951714467840/896445332509040650/unknown.png")
            return await interaction.response.send_message(
                embed=embed,
                view=Url(source_url, label="Open on GitHub", emoji="<:github:744345792172654643>")
            )

        for cmd in self.client.tree.walk_commands(guild=interaction.guild if command != "join" else None):
            if cmd.qualified_name == command:
                if isinstance(cmd, discord.app_commands.Group):
                    return await interaction.response.send_message(
                        f"{interaction.user.mention} I can't show the source code of a group command. Please specify a subcommand."
                    )
                obj = cmd
                break

        if obj is None:
            embed = discord.Embed(title=f"Couldn't find command.", description=mpl_advice, colour=discord.Colour.red())
            embed.set_image(
                url="https://cdn.discordapp.com/attachments/879251951714467840/896445332509040650/unknown.png"
            )
            return await interaction.response.send_message(
                embed=embed,
                view=Url(source_url, label="Open on GitHub", emoji="<:github:744345792172654643>")
            )

        src = obj.callback.__code__
        module = obj.callback.__module__
        filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        if not module.startswith("discord"):
            # not a built-in command
            location = os.path.relpath(filename).replace("\\", "/")
        else:
            location = module.replace(".", "/") + ".py"
            source_url = "https://github.com/Rapptz/discord.py"
            branch = "master"

        final_url = f"{source_url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}"
        embed = discord.Embed(title=f"Here's `{obj.name}`", description=mpl_advice)
        embed.set_image(url="https://cdn.discordapp.com/attachments/879251951714467840/896445332509040650/unknown.png")
        embed.set_footer(text=f"{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}")

        await interaction.response.send_message(
            embed=embed,
            view=Url(final_url, label=f"Here's {obj.name}", emoji="<:github:744345792172654643>")
        )

Cog = Various