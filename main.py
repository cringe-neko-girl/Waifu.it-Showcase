import os
import sys
import subprocess
import traceback
import asyncio
import aiohttp  # Import aiohttp for asynchronous HTTP requests
import logging  # Import the logging module
import discord
from discord.ext import commands
from aiohttp import web

from keep_alive import keep_alive
from Imports.discord_imports import *  # Ensure this is correctly defined
from Cogs.help import Help  # Import the Help class; ensure it's a subclass of HelpCommand

from colorama import Fore, Style  # Import Fore and Style explicitly
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

os.system("pip install --upgrade pip")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s',  # Define the log message format
    handlers=[
        logging.FileHandler("bot.log"),  # Log to a file
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)

class BotSetup(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=commands.when_mentioned_or(">"), intents=intents, shard_count=3, help_command=None)  # Set help_command to None initially
        self.mongoConnect = None  # Initialize the MongoDB connection attribute

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
            logger.info("Bot was stopped by the user.")
            await self.close()
        except Exception as e:
            traceback_string = traceback.format_exc()
            logger.error(f"An error occurred while logging in: {e}\n{traceback_string}")
            await self.close()

    async def setup(self):
        print("\n")
        print(Fore.BLUE + "・ ── Cogs/" + Style.RESET_ALL)
        await self.import_cogs("Cogs")
        print("\n")
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
                        # Check if the cog already exists before adding it
                        existing_cog = self.get_cog(obj_name)
                        if existing_cog:
                            await self.remove_cog(obj_name)  # Remove the existing cog
                            print(Fore.RED + f"│   │   Removed {obj_name} cog" + Style.RESET_ALL)
                            logger.info(f"Removed {obj_name} cog.")
                        
                        # Add the new cog
                        await self.add_cog(obj(self))
                        print(Fore.GREEN + f"│   │   └── {obj_name}" + Style.RESET_ALL)
                        logger.info(f"Added cog: {obj_name}")

async def check_rate_limit():
    url = "https://discord.com/api/v10/users/@me"  # Example endpoint to get the current user
    headers = {
        "Authorization": f"Bot {os.getenv('TOKEN')}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                remaining_requests = int(response.headers.get("X-RateLimit-Remaining", 1))
                rate_limit_reset_after = float(response.headers.get("X-RateLimit-Reset-After", 0))

                if remaining_requests <= 0:
                    logger.warning(f"Rate limit exceeded. Retry after {rate_limit_reset_after} seconds.")
                    print(f"Rate limit exceeded. Please wait for {rate_limit_reset_after} seconds before retrying.")
                    await asyncio.sleep(rate_limit_reset_after)
            else:
                logger.error(f"Failed to check rate limit. Status code: {response.status}")

async def main():
    bot = BotSetup()

    try:
        await check_rate_limit()  # Check rate limits before starting the bot
        await bot.start_bot()
    except Exception as e:
        traceback_string = traceback.format_exc()
        logger.error(f"An error occurred: {e}\n{traceback_string}")
    finally:
        await bot.close()
        logger.info("Bot closed.")

# Create a simple HTTP server to bind to a port
async def start_http_server():
    app = web.Application()
    app.router.add_get('/', lambda request: web.Response(text="Bot is running"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))  # Adapt for Render's PORT environment variable
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_http_server())  # Start the HTTP server
    loop.run_until_complete(main())  # Run the bot
