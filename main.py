import os
import traceback
import asyncio
import aiohttp  # For asynchronous HTTP requests
import logging  # For logging
import discord
from discord.ext import commands
from aiohttp import web
from dotenv import load_dotenv

from Imports.discord_imports import *  # Import Discord-specific utilities
from Cogs.help import Help  # Import the Help class; ensure it's a subclass of HelpCommand
from colorama import Fore, Style  # For colorful console outputs

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),  # Log to a file
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)

# Modern HTML for the status page
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot Status</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 0; }
        header { background-color: #1f1f1f; padding: 20px; text-align: center; font-size: 1.5em; color: #ffffff; }
        #log-container { padding: 20px; max-height: 80vh; overflow-y: auto; background-color: #1a1a1a; border: 1px solid #333; }
        footer { text-align: center; padding: 10px; font-size: 0.8em; background-color: #1f1f1f; color: #ffffff; }
    </style>
</head>
<body>
    <header>Discord Bot Status</header>
    <div id="log-container">
        <pre id="log-content">{log}</pre>
    </div>
    <footer>Powered by Render</footer>
    <script>
        const logContainer = document.getElementById("log-container");
        setInterval(() => {
            fetch('/logs').then(response => response.text()).then(data => {
                document.getElementById('log-content').textContent = data;
                logContainer.scrollTop = logContainer.scrollHeight;
            });
        }, 5000); // Fetch logs every 5 seconds
    </script>
</body>
</html>
"""

# Bot setup class
class BotSetup(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=commands.when_mentioned_or(">"), intents=intents, shard_count=3, help_command=None)
        self.mongoConnect = None  # MongoDB connection placeholder

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
            logger.error(f"Error occurred during bot startup: {e}\n{traceback.format_exc()}")
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
                            await self.remove_cog(obj_name)  # Remove existing cog
                            print(Fore.RED + f"│   │   Removed {obj_name} cog" + Style.RESET_ALL)
                            logger.info(f"Removed {obj_name} cog.")
                        await self.add_cog(obj(self))
                        print(Fore.GREEN + f"│   │   └── {obj_name}" + Style.RESET_ALL)
                        logger.info(f"Added cog: {obj_name}")

# Check rate limits
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

# HTTP server to monitor bot status
async def start_http_server():
    app = web.Application()

    async def status_page(request):
        with open("bot.log", "r") as log_file:
            logs = log_file.read()[-10000:]  # Show the last 10,000 characters of the log file
        return web.Response(text=HTML_PAGE.format(log=logs), content_type="text/html")

    async def fetch_logs(request):
        with open("bot.log", "r") as log_file:
            logs = log_file.read()[-10000:]
        return web.Response(text=logs, content_type="text/plain")

    app.router.add_get("/", status_page)
    app.router.add_get("/logs", fetch_logs)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logger.info("HTTP server running on port 8080.")

# Main entry point
async def main():
    bot = BotSetup()
    await asyncio.gather(
        check_rate_limit(),
        start_http_server(),
        bot.start_bot()
    )

if __name__ == "__main__":
    asyncio.run(main())
