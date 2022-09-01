import discord
import aiohttp

from discord.ext import commands

from . import cogs
from .static.constants import TOKEN, ServerInfo, GUILD_OBJECT, ACTIVITY_EVENT, TRIALS
from .utils.functions import is_dev

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

        self.server_info = ServerInfo.TEST if self.is_dev else ServerInfo.KITD

    def convert_to_timestamp(self, id: int, args: str = "f") -> str:
        """Turns a discord snowflake into a discord timestamp string"""
        return f"<t:{int((id >> 22) / 1000) + 1420070400}:{args}>"

    async def setup_hook(self):
        await self.load_extension("jishaku")
        # await self.tree.sync() # No global commands currently, though maybe in the future so leaving it in.
        await self.tree.sync(guild=GUILD_OBJECT) # Loads the commands for the server.

    async def _change_presence(self) -> None:
        """Changes the bot's presence to the current membercount"""
        a = discord.Activity(name=f"over {self.get_guild(self.server_info.ID).member_count} members", type=discord.ActivityType.watching)
        await self.change_presence(activity=a, status=discord.Status.online)

    async def on_ready(self) -> None:
        await self.wait_until_ready()
        await self._change_presence()

async def main():
    session = aiohttp.ClientSession()
    # Create the bot instance.
    bot = Bot(
        command_prefix="Will " if is_dev() else "Nico ",
        description="KITD's own discord bot",
        intents=discord.Intents.all(),
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