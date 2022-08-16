import discord

from discord.ext import commands

from bot.static.constants import GUILD_OBJECT
from bot.utils.interactions import Modal

class EmbedModal(Modal):

    def __init__(self, user_id: int, current_embed: discord.Embed):
        super().__init__(user_id, title="Feedback form")

        self.add_item(discord.ui.TextInput(label="Title", default=current_embed.title, required=True, max_length=256, style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(label="Description", default=current_embed.description, required=True, max_length=4000, style=discord.TextStyle.long))
        self.add_item(discord.ui.TextInput(label="Image url", default=current_embed.image.url if current_embed.image else None, required=False, style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(label="Colour", default=str(current_embed.colour) if current_embed.colour else None, required=False, style=discord.TextStyle.short))

class Owner(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

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
    def info_channel(self) -> discord.TextChannel:
        return self.guild.get_channel(self.client.server_info.INFO_CHANNEL)

    async def edit(self, interaction: discord.Interaction, message: discord.Message):
        """Edits an embed in #information"""
        if not interaction.user.id == self.guild.owner_id:
            return await interaction.response.send_message("You do not have permission to edit this embed", ephemeral=True)

        if not message.embeds:
            return await interaction.response.send_message("Message does not have an embed", ephemeral=True)

        embed: discord.Embed = message.embeds[0]
        modal = EmbedModal(interaction.user.id, embed)

        await interaction.response.send_modal(modal)
        await modal.wait()

        if modal.children[3]:
            try:
                embed.colour = discord.Colour.from_str(modal.children[3].value)
            except ValueError:
                embed.colour = None # If the colour is not valid I don't want all the other changes to be lost, so I just ignore it

        embed.title = modal.children[0].value
        embed.description = modal.children[1].value
        embed.set_image(url=modal.children[2].value)

        await message.edit(embed=embed)

        await modal.interaction.response.send_message("Message updated", ephemeral=True)

    owner = discord.app_commands.Group(name='owner', description="Owner commands", guild_ids=[GUILD_OBJECT.id])

Cog = Owner