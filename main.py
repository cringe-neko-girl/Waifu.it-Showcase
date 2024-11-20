import os
import sys
import subprocess
import traceback
import asyncio
import aiohttp  # For asynchronous HTTP requests
import logging  # For logging bot events
import discord
from discord.ext import commands
from aiohttp import web
import aiohttp_jinja2
import jinja2

from colorama import Fore, Style  # For colored console output
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

os.system("pip install --upgrade pip")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BotSetup(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=commands.when_mentioned_or(">"), intents=intents, shard_count=3, help_command=None)
        self.mongoConnect = None  # Initialize the MongoDB connection attribute
        self.app = None  # Aiohttp app

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
        await self.import_cogs("Events")
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
                            await self.remove_cog(obj_name)  # Remove the existing cog
                            print(Fore.RED + f"│   │   Removed {obj_name} cog" + Style.RESET_ALL)
                            logger.info(f"Removed {obj_name} cog.")
                        
                        await self.add_cog(obj(self))
                        print(Fore.GREEN + f"│   │   └── {obj_name}" + Style.RESET_ALL)
                        logger.info(f"Added cog: {obj_name}")

    async def start_http_server(self):
        """Start the HTTP server that serves templates and handles routes."""
        app = web.Application()

        # Set up Jinja2 template rendering
        aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))

        # Define routes
        app.router.add_get('/', self.index)  # Route for index page
        app.router.add_get('/ws', self.websocket_handler)  # WebSocket endpoint

        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.getenv("PORT", 8080))  # Adapt for Render's PORT environment variable
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        logger.info(f"HTTP server started on port {port}")

        self.app = app

    async def index(self, request):
        """Render the index.html template."""
        return aiohttp_jinja2.render_template('index.html', request, {})

    async def websocket_handler(self, request):
        """Handle WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        try:
            while True:
                msg = await ws.receive_json()
                print(msg)
        except:
            pass  # Handle disconnections or errors
        finally:
            print("WebSocket closed.")
        
        return ws


async def check_rate_limit():
    """Check the rate limit from Discord API."""
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


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_http_server())  # Start the HTTP server
    loop.run_until_complete(main())  # Run the bot
