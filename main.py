import os
import sys
import subprocess
import traceback
import asyncio
import logging
import aiohttp
from aiohttp import web
from dotenv import load_dotenv
from colorama import Fore, Style
import discord
from discord.ext import commands
from Imports.discord_imports import *  
from Cogs.help import Help  

load_dotenv()

os.system("pip install --upgrade pip")

logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler(sys.stdout)]  
)
logger = logging.getLogger(__name__)

class BotSetup(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=commands.when_mentioned_or(">"), 
            intents=intents, 
            shard_count=3, 
            help_command=None
        )
        self.mongoConnect = None 

    async def start_bot(self):
        await self.setup()  
        token = os.getenv('TOKEN')

        if not token:
            logger.error("No Discord bot token found. Please set the TOKEN environment variable.")
            return

        try:
            logger.info("Attempting to start the bot...")
            await self.start(token)
            logger.info("Bot started successfully.")
        except discord.LoginFailure:
            logger.error("Invalid bot token provided. Please verify the TOKEN environment variable.")
        except discord.HTTPException as e:
            logger.error(f"HTTP error occurred: {e}")
            await self.handle_rate_limit_error(e)
        except asyncio.CancelledError:
            logger.warning("The bot was cancelled.")
        except Exception as e:
            traceback_string = traceback.format_exc()
            logger.error(f"An unexpected error occurred while starting the bot: {e}\n{traceback_string}")
        finally:
            await self.close()

    async def handle_rate_limit_error(self, error):
        if isinstance(error, discord.HTTPException) and error.status == 429:
            retry_after = error.response.get('Retry-After', 5)
            logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
            await asyncio.sleep(retry_after)
            await self.start_bot()

    async def setup(self):
        await self.import_cogs("Cogs")
        await self.import_cogs("Events")

    async def import_cogs(self, dir_name):
        files_dir = os.listdir(dir_name)
        for filename in files_dir:
            if filename.endswith(".py"):
                logger.info(f"Importing cog: {filename}")
                module = __import__(f"{dir_name}.{os.path.splitext(filename)[0]}", fromlist=[""])
                for obj_name in dir(module):
                    obj = getattr(module, obj_name)
                    if isinstance(obj, commands.CogMeta):
                        existing_cog = self.get_cog(obj_name)
                        if existing_cog:
                            await self.remove_cog(obj_name)
                            logger.info(f"Removed existing cog: {obj_name}")
                        await self.add_cog(obj(self))
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
                    print(f"Rate limit exceeded. Please wait for {rate_limit_reset_after} seconds before retrying.")
                    await asyncio.sleep(rate_limit_reset_after)
            else:
                logger.error(f"Failed to check rate limit. HTTP Status: {response.status}")

async def start_http_server():
    app = web.Application()
    app.router.add_get('/', lambda request: web.Response(text="Bot is running"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))

    try:
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        logger.info(f"HTTP server started on port {port}")
        print(f"HTTP server started on port {port}")
    except OSError as e:
        logger.error(f"Failed to start HTTP server on port {port}: {e}")
        print(f"Failed to start HTTP server on port {port}. Error: {e}")

async def main():
    bot = BotSetup()

    try:
        logger.info("Checking rate limits before starting the bot...")
        await check_rate_limit()  
        await bot.start_bot()
    except Exception as e:
        traceback_string = traceback.format_exc()
        logger.error(f"An error occurred in main: {e}\n{traceback_string}")
    finally:
        await bot.close()
        logger.info("Bot has been closed.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(
            start_http_server(), 
            main()
        ))
    except Exception as e:
        logger.critical(f"Critical error in the main event loop: {e}")
        traceback.print_exc()
    finally:
        loop.close()
        logger.info("Event loop has been closed.")
