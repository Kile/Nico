import discord

from discord.ext import commands
from io import BytesIO
from typing import Union, List
from PIL import Image
from aiohttp.client_exceptions import InvalidURL, ClientResponseError

from bot.static.constants import GUILD_OBJECT

class Boosters(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        self.logo_image_url = "https://cdn.discordapp.com/attachments/1004512555538067476/1010537495148118056/KITD_Logo.gif"

    async def cog_load(self):
        print("Loaded boosters cog")
        res = await self.client.session.get(self.logo_image_url)
        image_bytes = await res.read()
        self._logo = image_bytes
        print(f"Successfully loaded logo")

    async def _get_bytes(self, image: Union[discord.Attachment, str]) -> BytesIO:
        if isinstance(image, discord.Attachment):
            return BytesIO(await image.read())
        else:
            res = await self.client.session.get(image)
            return BytesIO(await res.read())

    def _overlay(self, image: BytesIO) -> BytesIO:
        new_frames: List[Image.Image] = []
        gif = Image.open(BytesIO(self._logo))
        for i in range(gif.n_frames):
            gif.seek(i)
            background = Image.open(image).convert("RGBA")
            # resize background to fit the frame
            background = background.resize(gif.size, Image.ANTIALIAS)
            background.paste(gif, (0, 0), gif.convert("RGBA"))
            new_frames.append(background)

        # Save the frames to a buffer and return it
        buffer = BytesIO()
        new_frames[0].save(buffer, format="GIF", save_all=True, append_images=new_frames[1:], loop=0)
        buffer.seek(0)

        return buffer

    booster = discord.app_commands.Group(name="booster", description="Commands exclusive to boosters", guild_ids=[GUILD_OBJECT.id])

    @booster.command()
    @discord.app_commands.describe(image="The image to put the logo over", image_url="The url of the image to put the logo over")
    async def logo(self, interaction: discord.Interaction, image: discord.Attachment = None, image_url: str = None):
        """Gives you the logo of the server"""
        if not interaction.user.premium_since:
            return await interaction.response.send_message("You must be a booster to use this command")

        if not image and not image_url:
            return await interaction.response.send_message("You must provide an image to put the logo over")

        if image:
            image_bytes = await self._get_bytes(image)
        else:
            try:
                image_bytes = await self._get_bytes(image_url)
            except (InvalidURL, ClientResponseError):
                return await interaction.response.send_message("Invalid url!", ephemeral=True)

        resut = self._overlay(image_bytes)

        await interaction.response.send_message(file=discord.File(resut, filename="logo.gif"))

Cog = Boosters