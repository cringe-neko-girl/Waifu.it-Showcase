import os
import traceback
import asyncio
import aiohttp  # For asynchronous HTTP requests
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
from colorama import Fore, Style
from io import StringIO  # For in-memory log buffering

from Imports.discord_imports import *  # Import Discord-specific utilities
from Cogs.help import Help  # Ensure Help is a subclass of HelpCommand
from host_server import start_http_server  # Import the HTTP server function

# Load environment variables
load_dotenv()

# Configure logging
log_buffer = StringIO()
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(log_buffer),  # Log to in-memory buffer
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)

class BotSetup(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=commands.when_mentioned_or(">"), intents=intents, shard_count=3, help_command=None)
        self.mongoConnect = None

    async def start_bot(self):
        await self.setup()
        token = os.getenv('TOKEN')

        if not token:
            logger.error("No token found. Please set the TOKEN environment variable.")
            return

        try:
            await self.start(token)
            logger.info("Bot started successfully.")
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            await self.close()
        except Exception as e:
            logger.error(f"Error during bot startup: {e}\n{traceback.format_exc()}")
            await self.close()

    async def setup(self):
        print(Fore.BLUE + "・ ── Loading Cogs/" + Style.RESET_ALL)
        await self.import_cogs("Cogs")
        print(Fore.BLUE + "===== Setup Completed =====" + Style.RESET_ALL)

    async def import_cogs(self, dir_name):
        files_dir = os.listdir(dir_name)
        for filename in files_dir:
            if filename.endswith(".py"):
                print(Fore.BLUE + f"│   ├── {filename}" + Style.RESET_ALL)
                logger.info(f"Importing cog: {filename}")
                module = __import__(f"{dir_name}.{os.path.splitext(filename)[0]}", fromlist=[""])
                for obj_name in dir(module):
                    obj = getattr(module, obj_name)
                    if isinstance(obj, commands.CogMeta):
                        existing_cog = self.get_cog(obj_name)
                        if existing_cog:
                            await self.remove_cog(obj_name)
                            print(Fore.RED + f"│   │   Removed {obj_name} cog" + Style.RESET_ALL)
                            logger.info(f"Removed {obj_name} cog.")
                        await self.add_cog(obj(self))
                        print(Fore.GREEN + f"│   │   └── {obj_name}" + Style.RESET_ALL)
                        logger.info(f"Added cog: {obj_name}")

async def check_rate_limit():
    url = "https://discord.com/api/v10/users/@me"
    headers = {"Authorization": f"Bot {os.getenv('TOKEN')}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                remaining_requests = int(response.headers.get("X-RateLimit-Remaining", 1))
                rate_limit_reset_after = float(response.headers.get("X-RateLimit-Reset-After", 0))
                if remaining_requests <= 0:
                    logger.warning(f"Rate limit exceeded. Retry after {rate_limit_reset_after} seconds.")
                    await asyncio.sleep(rate_limit_reset_after)
            else:
                logger.error(f"Failed to check rate limits. Status code: {response.status}")

async def main():
    bot = BotSetup()
    await asyncio.gather(
        check_rate_limit(),
        start_http_server(log_buffer),  # Start the HTTP server
        bot.start_bot()  # Start the bot
    )

if __name__ == "__main__":
    asyncio.run(main())
