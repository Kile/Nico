import discord
import aiohttp

from discord.ext import commands

from . import cogs
from .static.constants import TOKEN, ServerInfo, GUILD_OBJECT
from .utils.functions import is_dev

import logging
import logging.handlers

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.ERROR)

handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
        await self.tree.sync() # No global commands currently, though maybe in the future so leaving it in.
        await self.tree.sync(guild=GUILD_OBJECT) # Loads the commands for the server.

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