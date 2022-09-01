import discord

from discord.ext import commands
from io import BytesIO
from typing import Union, List
from PIL import Image
from aiohttp.client_exceptions import InvalidURL, ClientResponseError

from bot.__init__ import Bot
from bot.static.constants import GUILD_OBJECT

class Boosters(commands.Cog):

    def __init__(self, client: Bot):
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
    
    def _intersect(self, list1: list, list2: list) -> bool:
        return len(set(list1).intersection(set(list2))) > 0

    premium = discord.app_commands.Group(name="premium", description="Commands exclusive to boosters/premium members", guild_ids=[GUILD_OBJECT.id])

    @premium.command()
    @discord.app_commands.describe(image="The image to put the logo over", image_url="The url of the image to put the logo over")
    async def logo(self, interaction: discord.Interaction, image: discord.Attachment = None, image_url: str = None):
        """Gives you the logo of the server"""
        if not self._intersect([r.id for r in interaction.user.roles], self.client.server_info.PREMIUM_ROLES) and not self.client.is_dev:
            return await interaction.response.send_message("You must be a booster or patreon to use this command. [Patreon ling](https://patreon.com/kitd)")

        if not image and not image_url:
            return await interaction.response.send_message("You must provide an image to put the logo over")

        if image:
            image_bytes = await self._get_bytes(image)
        else:
            try:
                image_bytes = await self._get_bytes(image_url)
            except (InvalidURL, ClientResponseError):
                return await interaction.response.send_message("Invalid url!", ephemeral=True)

        await interaction.response.defer()

        resut = self._overlay(image_bytes)

        await interaction.followup.send(file=discord.File(resut, filename="logo.gif"))

Cog = Boosters