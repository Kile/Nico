import discord
from discord.ext import commands

from bot.__init__ import Bot
from bot.utils.interactions import Modal

class Seasonal(commands.Cog):
    """A number of commands for events such as Valentines day"""

    def __init__(self, client: Bot):
        self.client = client

    @property
    def val_channel(self):
        return self.client.get_channel(self.client.server_info.VALENTINES_CHANNEL)

    def number_to_base(self, n: int, b: int = 10000) -> str:
        """Encrypt the author id so it is impossible to decipher by a human"""
        chars = "".join([chr(i) for i in range(b+1)][::-1])

        if n == 0:
            return [0]
        digits = []
        while n:
            digits.append(int(n % b))
            n //= b
        return "".join([chars[d] for d in digits[::-1]])

    @discord.app_commands.command()
    async def valentine(self, interaction: discord.Interaction, other: discord.Member):
        """Send a valentine to another member in the server"""

        if other == interaction.user:
            return await interaction.response.send_message("Hey... I am sure *someone* will send you a valentine! You don't have to do it yourself. Just give it a bit :3", ephemeral=True)

        # Create a modal to enter the valentine message
        modal = Modal(title="Valentine")
        message = discord.ui.TextInput(label="Message", placeholder="Enter your message here. What makes this person special?", style=discord.TextStyle.long)
        show = discord.ui.TextInput(label="Show you as sender", placeholder="Y/N", required=False)
        image = discord.ui.TextInput(label="Image", placeholder="Enter a link to an image to be displayed in your message", required=False)
        modal.add_item(message).add_item(show).add_item(image)

        await interaction.response.send_modal(modal)

        # Wait for the user to submit the modal
        await modal.wait()

        # Check if the user wants to show their name
        show = show.value.lower() == "y" if show.value else False

        encrypted_author = self.number_to_base(interaction.user.id)
        view = discord.ui.View()
        button = discord.ui.Button(label="Send with ❤️", style=discord.ButtonStyle.red, disabled=True, custom_id=encrypted_author)
        view.add_item(button)

        embed = discord.Embed.from_dict({
            "title": "Valentine for " + other.display_name,
            "description": message.value,
            "color": discord.Colour.red().value,
            "image": {"url": image.value} if image.value else None,
        })        
        if show:
            embed.set_author(name="By " + interaction.user.display_name, icon_url=interaction.user.avatar.url)

        await self.val_channel.send(content=other.mention,embed=embed, view=view)
        await modal.interaction.response.send_message("Your valentine has been sent!", ephemeral=True)

Cog = Seasonal