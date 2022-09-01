import discord

from discord.ext import commands

from typing import Literal, Union, Tuple

from bot.__init__ import Bot
from bot.cogs.trials import Trials
from bot.static.constants import GUILD_OBJECT, CONSTANTS, TRIALS
from bot.utils.interactions import Modal, View, Button

class UpdateModal(Modal):

    def __init__(self, user_id: int):
        super().__init__(user_id, title="Update")
        self.add_item(discord.ui.TextInput(label="What's new?", placeholder="Made Nico event better (although impossible)", required=True, max_length=4000, style=discord.TextStyle.long))


class EmbedModal(Modal):

    def __init__(self, user_id: int, current_embed: discord.Embed):
        super().__init__(user_id, title="Embed editing menu")

        self.add_item(discord.ui.TextInput(label="Title", default=current_embed.title, required=False, max_length=256, style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(label="Description", default=current_embed.description, required=False, max_length=4000, style=discord.TextStyle.long))
        self.add_item(discord.ui.TextInput(label="Image url", default=current_embed.image.url if current_embed.image else None, required=False, style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(label="Colour", default=str(current_embed.colour) if current_embed.colour else None, required=False, style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(label="Footer", default=current_embed.footer.text if current_embed.footer else None, required=False, style=discord.TextStyle.short))

class ContentModal(Modal):
    
        def __init__(self, user_id: int, current_content: str):
            super().__init__(user_id, title="Message editing menu")
    
            self.add_item(discord.ui.TextInput(label="Content", default=current_content, required=False, max_length=4000, style=discord.TextStyle.long))

class Owner(commands.Cog):

    def __init__(self, client: Bot):
        self.client = client
        self.update_banner_url = "https://cdn.discordapp.com/attachments/1004512555538067476/1008487606893416538/20220814_234634_0000.png"

        menu = discord.app_commands.ContextMenu(
            name="edit",
            callback=self.edit,
            guild_ids=[GUILD_OBJECT.id]
            # type=discord.AppCommandType.message
        )

        self.client.tree.add_command(menu)

    async def cog_load(self):
        print("Loaded owner cog")

    @property
    def guild(self) -> discord.Guild:
        return self.client.get_guild(self.client.server_info.ID)

    @property
    def update_channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.UPDATE_CHANNEL)

    async def _new_embed(self, old_embed: discord.Embed, interaction: discord.Interaction) -> Union[Tuple[discord.Embed, discord.Interaction], None]:

        modal = EmbedModal(interaction.user.id, old_embed)
        await interaction.response.send_modal(modal)

        await modal.wait()

        if modal.timed_out:
            return

        try:
            colour = discord.Colour.from_str(modal.values[3])
        except (ValueError, IndexError):
            colour = None

        embed = discord.Embed.from_dict({
            "title": modal.values[0] or "", 
            "description": modal.values[1] or "", 
            "color": int(colour) if colour else 0,
            "image": {"url": modal.values[2]},
        })
        if modal.values[4]:
            embed.set_footer(text=modal.values[4])

        return (embed, modal.interaction)

    async def edit(self, interaction: discord.Interaction, message: discord.Message):
        """Edits an embed in #information"""
        if not interaction.user.id == self.guild.owner_id:
            return await interaction.response.send_message("You do not have permission to edit this embed", ephemeral=True)
        if not message.author.id == self.client.user.id:
            return await interaction.response.send_message("You can only edit messages sent by the me", ephemeral=True)

        view = View(interaction.user.id, timeout=60)
        view.add_item(Button(label="Message content", style=discord.ButtonStyle.blurple, custom_id="content"))

        for pos, _ in enumerate(message.embeds):
            view.add_item(Button(label=f"Embed {pos+1}", style=discord.ButtonStyle.blurple, custom_id=str(pos)))  

        view.add_item(Button(emoji="\U00002795", label="Add embed", style=discord.ButtonStyle.green, custom_id="add"))
        view.add_item(Button(emoji="\U00002796", label="Remove embed", style=discord.ButtonStyle.red, custom_id="remove"))

        await interaction.response.send_message("Please choose what to edit", view=view, ephemeral=True)

        await view.wait()

        if view.timed_out:
            return await view.disable(await interaction.original_response())

        if view.value == "content":
            modal = ContentModal(interaction.user.id, message.content)
            await view.interaction.response.send_modal(modal)

            await modal.wait()

            if modal.timed_out:
                return

            await message.edit(content=modal.values[0])
            await modal.interaction.response.send_message(":thumbsup: Content updated", ephemeral=True)

        elif view.value.isdigit():
            old_embed = message.embeds[int(view.value)]
            new = await self._new_embed(old_embed, view.interaction)

            if not new: return

            new_embed, interaction = new

            message.embeds[int(view.value)] = new_embed
            await message.edit(embeds=message.embeds)
            await interaction.response.send_message(":thumbsup: Embed updated", ephemeral=True)

        elif view.value == "add":
            new = await self._new_embed(discord.Embed(), view.interaction)

            if not new: return

            new_embed, interaction = new

            message.embeds.append(new_embed)
            await message.edit(embeds=message.embeds)
            await interaction.response.send_message(":thumbsup: Embed added", ephemeral=True)

        elif view.value == "remove":

            await view.disable(await interaction.original_response(), respond=False)

            if len(message.embeds) == 0:
                return await interaction.response.send_message("There are no embeds to remove", ephemeral=True)

            remove_view = View(interaction.user.id, timeout=60)

            for pos, _ in enumerate(message.embeds):
                remove_view.add_item(Button(label=f"Embed {pos+1}", style=discord.ButtonStyle.red, custom_id=str(pos)))

            await view.interaction.response.send_message("Please choose what embed to remove", view=remove_view, ephemeral=True)

            await remove_view.wait()

            if remove_view.timed_out:
                return await remove_view.disable(await view.interaction.original_response())

            message.embeds.pop(int(remove_view.value))
            await message.edit(embeds=message.embeds)
            await remove_view.disable(await view.interaction.original_response(), respond=False)
            return await remove_view.interaction.response.send_message(":thumbsup: Embed removed", ephemeral=True)

        await view.disable(await view.interaction.original_response())

    owner = discord.app_commands.Group(name='owner', description="Owner commands", guild_ids=[GUILD_OBJECT.id])

    @owner.command()
    async def update(self, interaction: discord.Interaction):
        """Submit an update about Nico with this command"""
        if not interaction.user.id == self.guild.owner_id:
            return await interaction.response.send_message("You must be the server owner to use this command", ephemeral=True)

        modal = UpdateModal(interaction.user.id)
        await interaction.response.send_modal(modal)
        await modal.wait()

        update = modal.children[0].value
        embed = discord.Embed.from_dict({
            "title": "**New Nico update**",
            "description": update,
            "color": 0xfbafaf,
            "image": {
                "url": self.update_banner_url
            },
        })
        await self.update_channel.send(content="<@&1004871752037453866>", embed=embed)
        await modal.interaction.response.send_message(":white_check_mark: Update published!", ephemeral=True)

    @owner.command()
    @discord.app_commands.describe(status="Wether to open or close trials")
    async def trialstatus(self, interaction: discord.Interaction, status: Literal["open", "close"]):
        """Opens or close the trials for staff positions"""

        if not interaction.user.id == self.guild.owner_id:
            return await interaction.response.send_message("You must be the server owner to use this command", ephemeral=True)

        if TRIALS == ("open" == status):
            return await interaction.response.send_message("Trials are already " + status + ("d" if status == "close" else ""), ephemeral=True)

        data = CONSTANTS.find_one({"_id": "trials"})

        await interaction.response.defer(ephemeral=True)

        if not data:
            CONSTANTS.insert_one({"_id": "trials", "active": status == "open"})
        else:
            CONSTANTS.update_one({"_id": "trials"}, {"$set": {"active": status == "open"}})

        if status == "close":
            await self.client.remove_cog("Trials") # Remove the trials command if the trials are closed
            await self.client.tree.sync(guild=GUILD_OBJECT)

            await interaction.followup.send(":white_check_mark: Trials closed", ephemeral=True)

        else:
            await self.client.add_cog(Trials(self.client))
            await self.client.tree.sync(guild=GUILD_OBJECT)

            await interaction.followup.send(":white_check_mark: Trials opened", ephemeral=True)


Cog = Owner