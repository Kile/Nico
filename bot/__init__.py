import discord
import aiohttp

from discord.ext import commands
from urllib.parse import quote

from . import cogs
from .static.constants import TOKEN, ServerInfo, GUILD_OBJECT, ACTIVITY_EVENT, TRIALS, CONSTANTS
from .utils.functions import is_dev
# from .utils.interactions import PersistentVerificationView

import logging, sys

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
logging.getLogger('discord.http').setLevel(logging.ERROR)

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='[%(asctime)s:%(levelname)s:%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.invite = "https://discord.com/oauth2/authorize?client_id=737723077978488973&scope=bot&permissions=8&applications.commands"
        self.is_dev = is_dev() # Checks if the bot is a dev bot

        self.server_info = ServerInfo.TEST if self.is_dev else ServerInfo.NSS

        self.session: aiohttp.ClientSession = None
        self.translate_cache = {}

    def convert_to_timestamp(self, id: int, args: str = "f") -> str:
        """Turns a discord snowflake into a discord timestamp string"""
        return f"<t:{int((id >> 22) / 1000) + 1420070400}:{args}>"

    async def setup_hook(self):
        await self.load_extension("jishaku")
        await self.tree.sync() # No global commands currently, though maybe in the future so leaving it in.
        await self.tree.sync(guild=GUILD_OBJECT) # Loads the commands for the server.

        # application_views = CONSTANTS.find_one({"_id": "pending_applications"})

        # if application_views is None: return

        # for view in application_views["ids"]:
        #     self.add_view(PersistentVerificationView(view["applicant"]), message_id=view["message"])

    async def _change_presence(self) -> None:
        """Changes the bot's presence to the current membercount"""
        a = discord.Activity(name=f"over {self.get_guild(self.server_info.ID).member_count} members", type=discord.ActivityType.watching)
        await self.change_presence(activity=a, status=discord.Status.online)

    async def on_ready(self) -> None:
        await self.wait_until_ready()
        await self._change_presence()

    async def translate_callback(self, interaction: discord.Interaction) -> None:
        cache_id = interaction.data["custom_id"].split(":")[1]
        target = interaction.locale.value.split("-")[0]

        if "en" == target:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="You silly billy!",
                    description="You are already using the correct language!")
                , 
                ephemeral=True
            )

        if self.translate_cache.get(cache_id, False) and self.translate_cache[cache_id].get(target, False):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Translation",
                    description=self.translate_cache[cache_id][target])
                , 
                ephemeral=True
            )
        
        await interaction.response.defer(thinking=True, ephemeral=True)

        original_message = interaction.message
        has_embed = not not original_message.embeds
        text = original_message.content if not has_embed else original_message.embeds[0].description

        chunks = text.split("\n")
        formatted_chunks = []
        for chunk in chunks:
            if len(formatted_chunks) == 0:
                formatted_chunks.append(chunk)
            elif len(formatted_chunks[-1]) + len(chunk) > 500:
                formatted_chunks.append(chunk)
            else:
                formatted_chunks[-1] += "\n" + chunk

        result = ""
        for chunk in formatted_chunks:
            coded_text = quote(text, safe="")

            res = await self.session.get(
                "http://api.mymemory.translated.net/get?q="
                + coded_text
                + "&langpair=en|"
                + target.lower()
            )

            if not (res.status == 200):
                return await interaction.edit_original_response(content=":x: " + await res.text(), ephemeral=True)

            translation = await res.json()
            if translation["responseStatus"] != 200:   
                return await interaction.edit_original_response(content=":x: " + translation["responseDetails"], ephemeral=True)
            full_translation = translation["responseData"]["translatedText"]
            
            result += full_translation + "\n"

        self.translate_cache[cache_id] = self.translate_cache.get(cache_id, {})
        self.translate_cache[cache_id][target] = result
        embed = discord.Embed(
            title="Translation",
            description=result
        )
        await interaction.edit_original_response(
            embed=embed,
        )

async def main():
    session = aiohttp.ClientSession()
    # Create the bot instance.
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    bot = Bot(
        command_prefix="Will " if is_dev() else "Nico ",
        description="Nico's Safe Space's own discord bot",
        intents=intents,
        session=session
    )
    bot.session = session

    # Setup cogs.
    for cog in cogs.all_cogs:
        if cog.__name__.lower() == "event" and not ACTIVITY_EVENT:
            continue

        if cog.__name__.lower() == "trials" and not TRIALS:
            continue

        await bot.add_cog(cog.Cog(bot))

    await bot.start(TOKEN)
    
    # if bot.is_dev: # runs the api locally if the bot is in dev mode
    #     loop = asyncio.get_event_loop()
    #     loop.create_task(bot.start(TOKEN))
    #     Thread(target=loop.run_forever).start()
    #     app.run(host="0.0.0.0", port=PORT)
    # else:
    #     # Start the bot.
    #     bot.run(TOKEN)