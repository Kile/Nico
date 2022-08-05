import discord

from typing import Union
from datetime import timedelta

from discord.ext import commands

from bot.__init__ import is_dev
from bot.static.constants import ServerInfo

class UntrustView(discord.ui.View):

    def __init__(
        self, 
        user_id: int, 
        target: discord.Member, 
        channel: discord.TextChannel,
        reason: str
        ):
        super().__init__()

        self.user_id = user_id
        self.channel = channel
        self.target = target
        self.reason = reason
        self.msg = None

        self.votes = {
            "yes": [],
            "no": []
        }
        self.timed_out = False

    async def disable(self, msg:discord.Message) -> Union[discord.Message, None]:
        """"Disables the children inside of the view"""
        if not [c for c in self.children if not c.disabled]: # if every child is already disabled, we don't need to edit the message again
            return

        for c in self.children:
            c.disabled = True

        if self.interaction and not self.interaction.response.is_done():
            await self.interaction.response.edit_message(view=self)
        else:
            await msg.edit(view=self)

    async def on_timeout(self) -> None:
        self.timed_out = True
        embed = discord.Embed.from_dict({
            "title": "Unsuccessfull untrust vote",
            "fields": [
                {"name": "User", "value": self.target.mention},
                {"name": "Vote initiated by", "value": "<@{}>".format(self.user_id)},
                {"name": "Reason", "value": self.reason},
                {"name": "Voted for by", "value": "\n".join([f"<@{id}>" for id in self.votes["yes"]])  or "No votes for."},
                {"name": "Voted against by", "value": "\n".join([f"<@{id}>" for id in self.votes["no"]])}
            ],
            "color": int(discord.Color.red()),
            "description": "[Jump to original message](" +  self.msg.jump_url + ")"
        })
        await self.channel.send(embed=embed)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.target == interaction.user:
            await interaction.response.send_message("You cannot vote in a vote regarding yourself!", ephemeral=True)
            return False

        if self.user_id == interaction.user.id:
            await interaction.response.send_message("You cannot vote on a vote you started!", ephemeral=True)
            return False

        if not (ServerInfo.TEST.VERIFIED_ROLE if is_dev() else ServerInfo.KITD.VERIFIED_ROLE) in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message("You need to have the verified role to vote!", ephemeral=True)
            return False

        return True
        
    @discord.ui.button(label="Untrust (0/3)", style=discord.ButtonStyle.red)
    async def untrust(self, interaction: discord.Interaction, _: discord.ui.Button):

        if interaction.user.id in self.votes["yes"]:
            self.votes["yes"].remove(interaction.user.id)
        else:
            self.votes["yes"].append(interaction.user.id)

            if interaction.user.id in self.votes["no"]: # If untrust is pressed while user has pressed abort before, their abort vote is removed
                self.votes["no"].remove(interaction.user.id)
                self.children[1].label = f"Abort ({len(self.votes['no'])}/3)"

        if len(self.votes["yes"]) >= 3:
            await self.target.timeout(timedelta(days=1)) # Timeout user for 24 hours
            await interaction.response.edit_message(content=f"Successfull vote to timeout user! {self.target.mention} has been timeouted for 24h", view=None, embeds=[])
            embed = discord.Embed.from_dict({
                "title": "Successfull untrust vote",
                "fields": [
                    {"name": "User", "value": self.target.mention},
                    {"name": "Vote initiated by", "value": "<@{}>".format(self.user_id)},
                    {"name": "Reason", "value": self.reason},
                    {"name": "Voted for by", "value": "\n".join([f"<@{id}>" for id in self.votes["yes"]])},
                    {"name": "Voted against by", "value": "\n".join([f"<@{id}>" for id in self.votes["no"]]) or "No votes against."}
                ],
                "color": int(discord.Color.red()),
                "description": "[description](" +  self.msg.jump_url + ")"
            })
            await self.channel.send(embed=embed)
            return self.stop()

        else:
            self.children[0].label = f"Untrust ({len(self.votes['yes'])}/3)"
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Abort (0/3)", style=discord.ButtonStyle.green)
    async def abort(self, interaction: discord.Interaction, _: discord.ui.Button):

        if interaction.user.id in self.votes["no"]:
            self.votes["no"].remove(interaction.user.id)
        else:
            self.votes["no"].append(interaction.user.id)
            if interaction.user.id in self.votes["yes"]: # If abort is pressed while user has pressed untrust before, their untrust vote is removed
                self.votes["yes"].remove(interaction.user.id)
                self.children[0].label = f"Untrust ({len(self.votes['yes'])}/3)"

        if len(self.votes["no"]) >= 3:
            await interaction.response.edit_message(content=f"Unsuccessfull vote to timeout user! Vote to timeout {self.target.mention} has been aborted", view=None, embeds=[])
            embed = discord.Embed.from_dict({
                "title": "Unsuccessfull untrust vote",
                "fields": [
                    {"name": "User", "value": self.target.mention},
                    {"name": "Vote initiated by", "value": "<@{}>".format(self.user_id)},
                    {"name": "Reason", "value": self.reason},
                    {"name": "Voted for by", "value": "\n".join([f"<@{id}>" for id in self.votes["yes"]])  or "No votes for."},
                    {"name": "Voted against by", "value": "\n".join([f"<@{id}>" for id in self.votes["no"]])}
                ],
                "color": int(discord.Color.red()),
                "description": "[Jump to original message](" +  self.msg.jump_url + ")"
            })
            await self.channel.send(embed=embed)
            return self.stop()

        else:
            self.children[1].label = f"Abort ({len(self.votes['no'])}/3)"
            await interaction.response.edit_message(view=self)

class Untrust(commands.Cog):

    def __init__(self, client):
        self.client = client

    @property
    def guild(self):
        return self.client.get_guild(self.client.server_info.ID)

    @property
    def channel(self):
        return self.guild.get_channel(self.client.server_info.UNTRUSTED_CHANNEL)

    async def cog_load(self):
        print("Loaded untrust cog")

    @discord.app_commands.command()
    async def untrust(self, interaction: discord.Interaction, target: discord.Member, reason: str = "No reason provided"):
        """Start a vote to timeout a user for 24h."""
        if target == interaction.user:
            return await interaction.response.send_message("You cannot untrust yourself!", ephemeral=True)

        if self.guild.me.top_role < target.top_role or target.guild_permissions.administrator or self.guild.owner == target:
            return await interaction.response.send_message("This user cannot be untrusted!", ephemeral=True)

        view = UntrustView(interaction.user.id, target, self.channel, reason)

        embed = discord.Embed.from_dict({
            "title": "Untrust vote",
            "descripton": f"{interaction.user.mention} wants to untrust {target.mention} for {reason}. Verified members please vote on this vote.",
            "fields": [
                {"name": "User", "value": target.mention},
                {"name": "Vote initiated by", "value": "<@{}>".format(interaction.user.id)},
                {"name": "Reason", "value": reason}
            ],
            "color": int(discord.Color.red())
        })
        await interaction.response.send_message(embed=embed, view=view)
        view.msg = await interaction.original_message()

        await view.wait()

        if view.timed_out:
            await interaction.channel.send("Vote timed out.", reference=view.msg)

        await view.disable(view.msg)

Cog = Untrust

async def setup(client):
    await client.add_cog(Untrust(client))