import discord
from discord.ext import commands
import aiohttp_jinja2
import jinja2
from aiohttp import web

class WebEventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Event triggered when the bot is ready."""
        print(f"Bot has logged in as {self.bot.user}")

    async def start_http_server(self):
        """Start the HTTP server that serves the templates."""
        app = web.Application()

        # Set up Jinja2 template rendering
        aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))

        # Define routes
        app.router.add_get('/', self.index)  # Route for index page
        app.router.add_get('/ws', self.websocket_handler)  # WebSocket endpoint if needed

        runner = web.AppRunner(app)
        await runner.setup()
        port = 8080  # Or get it from environment variables
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"HTTP server running on port {port}")

    async def index(self, request):
        """Render the index.html template."""
        return aiohttp_jinja2.render_template('index.html', request, {})

    async def websocket_handler(self, request):
        """Handle WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # WebSocket handling logic goes here (optional)
        # Example: receiving and sending messages
        try:
            while True:
                msg = await ws.receive_json()
                print(msg)  # Handle incoming WebSocket messages
        except:
            pass  # Handle disconnections or errors
        finally:
            print("WebSocket closed.")
        
        return ws

    @commands.command(hidden=True)
    async def start_http(self, ctx):
        """Start the HTTP server from a command."""
        await self.start_http_server()
        await ctx.send("HTTP server has started!")

# Setup function to add the cog to the bot
def setup(bot):
    bot.add_cog(WebEventCog(bot))
