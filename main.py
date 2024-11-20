import os
import sys
import subprocess
import traceback
import asyncio
import aiohttp
import logging
import discord
from discord.ext import commands
from aiohttp import web
from aiohttp.web import WebSocketResponse
from dotenv import load_dotenv
import aiohttp_jinja2
import jinja2

from Imports.discord_imports import *  # Ensure this is correctly defined
from Cogs.help import Help  # Import the Help class; ensure it's a subclass of HelpCommand
from colorama import Fore, Style

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

# Global variable to hold active websockets
websockets = []

class BotSetup(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=commands.when_mentioned_or(">"), intents=intents, shard_count=3, help_command=None)
        self.mongoConnect = None  # MongoDB connection (if needed)

    async def start_bot(self):
        # Ensure the bot is set up correctly
        logger.info("Starting bot setup process...")
        await self.setup()
        token = os.getenv('TOKEN')
        
        if not token:
            logger.error("No token found. Please set the TOKEN environment variable.")
            return
        
        try:
            logger.info("Starting bot...")
            await self.start(token)
            logger.info("Bot started successfully.")
        except discord.LoginFailure:
            logger.error("Invalid token or unable to log in.")
        except KeyboardInterrupt:
            logger.info("Bot was stopped by the user.")
            await self.close()
        except Exception as e:
            logger.error(f"An error occurred: {e}\n{traceback.format_exc()}")
            await self.close()

    async def setup(self):
        # Setup the bot including cogs
        logger.info("Starting bot setup...")
        await self.import_cogs("Cogs")
        logger.info("Bot setup completed.")

    async def import_cogs(self, dir_name):
        # Attempt to load cogs dynamically from a specified directory
        files_dir = os.listdir(dir_name)
        for filename in files_dir:
            if filename.endswith(".py"):
                try:
                    # Log the cog being imported
                    logger.info(f"Attempting to import cog: {filename}")
                    cog_name = os.path.splitext(filename)[0]
                    await self.load_cog(cog_name, dir_name)
                except Exception as e:
                    logger.error(f"Failed to load cog {filename}: {e}")

    async def load_cog(self, cog_name, dir_name):
        try:
            # Load the cog
            await self.load_extension(f"{dir_name}.{cog_name}")
            logger.info(f"Cog {cog_name} loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading cog {cog_name}: {e}")

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

# Web server to serve the frontend
async def start_http_server():
    app = web.Application()

    # Setup Jinja2 template engine
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("templates"))

    # Define your routes
    app.router.add_get('/', index)  # Render index.html
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
            print(msg)  # Handle any messages sent from frontend
    except:
        pass  # Handle errors or disconnections
    finally:
        websockets.remove(ws)  # Remove WebSocket on disconnect

# Main entry to run the bot and web server
async def main():
    bot = BotSetup()

    try:
        logger.info("Starting bot and web server...")
        await bot.start_bot()
    except Exception as e:
        logger.error(f"An error occurred: {e}\n{traceback.format_exc()}")
    finally:
        await bot.close()
        logger.info("Bot closed.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_http_server())  # Start the HTTP server
    loop.run_until_complete(main())  # Run the bot
