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
        self.logo_image_url = "https://cdn.discordapp.com/attachments/761621578458202122/1054740365841801296/logo_transparent.gif"
        self.old_logo_image_url = "https://cdn.discordapp.com/attachments/1004512555538067476/1010537495148118056/KITD_Logo.gif"

    async def cog_load(self):
        print("Loaded boosters cog")
        res = await self.client.session.get(self.old_logo_image_url)
        image_bytes = await res.read()
        self._old_logo = image_bytes

        res2 = await self.client.session.get(self.logo_image_url)
        image_bytes2 = await res2.read()
        self._logo = image_bytes2
        print(f"Successfully loaded logos")

    async def _get_bytes(self, image: Union[discord.Attachment, str]) -> BytesIO:
        if isinstance(image, discord.Attachment):
            return BytesIO(await image.read())
        else:
            res = await self.client.session.get(image)
            return BytesIO(await res.read())

    async def _find_dominant_color(self, url: str) -> str:
        """Finds the dominant color of an image and returns it as an rgb tuple"""
        #Resizing parameters
        width, height = 150,150
        obj = await self._get_bytes(url)
        image = Image.open(obj)
        image = image.resize((width, height),resample = 0)
        #Get colors from image object
        pixels = image.getcolors(width * height)
        #Sort them by count number(first element of tuple)
        sorted_pixels = sorted(pixels, key=lambda t: t[0])
        #Get the most frequent color
        dominant_color = sorted_pixels[-1][1]
        return dominant_color

    def _overlay(self, image: BytesIO, logo: bytes) -> BytesIO:
        new_frames: List[Image.Image] = []
        gif: Image.Image = Image.open(BytesIO(logo))
        duration = gif.info["duration"]
        for i in range(gif.n_frames):
            gif.seek(i)
            background: Image.Image = Image.open(image).convert("RGBA")
            # resize background to fit the frame
            background = background.resize(gif.size, Image.ANTIALIAS)
            background.paste(gif, (0, 0), gif.convert("RGBA"))
            new_frames.append(background)

        if len(new_frames) == 0:
            raise ValueError("No frames found in the GIF")

        # Save the frames to a buffer and return it
        buffer = BytesIO()
        new_frames[0].save(buffer, format="GIF", save_all=True, append_images=new_frames[1:], duration=duration,loop=0)
        buffer.seek(0)

        return buffer
    
    def _intersect(self, list1: list, list2: list) -> bool:
        return len(set(list1).intersection(set(list2))) > 0

    premium = discord.app_commands.Group(name="premium", description="Commands exclusive to boosters/premium members", guild_ids=[GUILD_OBJECT.id])

    @premium.command()
    @discord.app_commands.describe(image="The image to put the logo over", image_url="The url of the image to put the logo over")
    async def old_logo(self, interaction: discord.Interaction, image: discord.Attachment = None, image_url: str = None):
        """Put any image behind the old logo of the server"""
        if not self._intersect([r.id for r in interaction.user.roles], self.client.server_info.PREMIUM_ROLES) and not self.client.is_dev:
            return await interaction.response.send_message("You must be a premium member or booster to use this command. [Premium page]( https://canary.discord.com/channels/710871326557995079/role-subscriptions)")

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

        resut = self._overlay(image_bytes, self._old_logo)

        await interaction.followup.send(file=discord.File(resut, filename="old_logo.gif"))

    @premium.command()
    @discord.app_commands.describe(image="The image to put the logo over", image_url="The url of the image to put the logo over")
    async def logo(self, interaction: discord.Interaction, image: discord.Attachment = None, image_url: str = None):
        """Put any image behind the logo of the server"""
        if not self._intersect([r.id for r in interaction.user.roles], self.client.server_info.PREMIUM_ROLES) and not self.client.is_dev:
            return await interaction.response.send_message("You must be a premium member or booster to use this command. [Premium page]( https://canary.discord.com/channels/710871326557995079/role-subscriptions)")

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

        resut = self._overlay(image_bytes, self._logo)

        await interaction.followup.send(file=discord.File(resut, filename="logo.gif"))

    @premium.command()
    async def catboy(self, interaction: discord.Interaction):
        """Shows a random catboy image out of a collection of 338 images"""
        if not self._intersect([r.id for r in interaction.user.roles], self.client.server_info.PREMIUM_ROLES) and not self.client.is_dev:
            return await interaction.response.send_message("You must be a premium member or booster to use this command. [Premium page]( https://canary.discord.com/channels/710871326557995079/role-subscriptions)")

        url = "https://api.catboys.com/"

        image = await self.client.session.get(url + "img")
        image = await image.json()

        if image["error"] != "none":
            return await interaction.response.send_message("An error occurred while getting the image: " + image["error"])

        quote = await self.client.session.get(url + "catboy")
        quote = await quote.json()

        if quote["error"] != "none":
            return await interaction.response.send_message("An error occurred while getting the quote: " + quote["error"])

        color = discord.Color.from_rgb(*(await self._find_dominant_color(image["url"])))
        # Unecessary? Maybe. But is a premium command after all
        embed = discord.Embed(title="Catboy", description=quote["response"], color=color)
        embed.set_image(url=image["url"])
        if image["artist"] != "unknown":
            embed.set_footer(text=f"Art by {image['artist']}")

        await interaction.response.send_message(embed=embed)

Cog = Boosters