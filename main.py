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
from aiohttp.web import WebSocketResponse
from dotenv import load_dotenv
import aiohttp_jinja2
import jinja2

from Imports.discord_imports import *  # Ensure this is correctly defined
from Cogs.help import Help  # Import the Help class; ensure it's a subclass of HelpCommand

from colorama import Fore, Style  # Import Fore and Style explicitly

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

# Global variable to hold active websockets
websockets = []

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

    # WebSocket event listeners for frontend updates
    async def send_to_websockets(self, data):
        """Send status or log data to all active websockets."""
        for ws in websockets:
            try:
                await ws.send_json(data)
            except:
                pass  # Handle disconnections or other errors

    # Bot event handlers
    async def on_ready(self):
        logger.info(f"Bot is ready as {self.user}")
        await self.send_to_websockets({"status": "Online", "message": f"Bot is ready as {self.user}"})

    async def on_disconnect(self):
        logger.info("Bot has disconnected.")
        await self.send_to_websockets({"status": "Offline", "message": "Bot has disconnected."})

    async def on_message(self, message):
        if message.author.bot:
            return

        logger.info(f"Message received in #{message.channel.name}: {message.content}")
        await self.send_to_websockets({"status": "Message", "message": f"New message from {message.author.name}: {message.content}"})

    async def on_error(self, event, *args, **kwargs):
        logger.error(f"An error occurred in event {event}: {traceback.format_exc()}")
        await self.send_to_websockets({"status": "Error", "message": f"Error in event {event}"})

    async def on_member_join(self, member):
        logger.info(f"New member joined: {member.name}")
        await self.send_to_websockets({"status": "Member Join", "message": f"New member joined: {member.name}"})

    async def on_member_remove(self, member):
        logger.info(f"Member left: {member.name}")
        await self.send_to_websockets({"status": "Member Leave", "message": f"Member left: {member.name}"})

# Create a simple HTTP server to bind to a port
async def start_http_server():
    app = web.Application()

    # Setup Jinja2 template engine
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("templates"))

    # Define your routes
    app.router.add_get('/', index)  # This will render the index.html
    app.router.add_get('/ws', websocket_handler)  # WebSocket endpoint

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))  # Adapt for Render's PORT environment variable
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def index(request):
    """Render the index.html template"""
    return aiohttp_jinja2.render_template('index.html', request, {})

async def websocket_handler(request):
    """Handle WebSocket connections."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # Add WebSocket connection to list
    websockets.append(ws)

    try:
        while True:
            msg = await ws.receive_json()
            # You can implement logic to handle messages from the frontend here
            print(msg)
    except:
        pass  # Handle errors or disconnections
    finally:
        websockets.remove(ws)  # Remove WebSocket on disconnect

async def main():
    bot = BotSetup()

    try:
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
