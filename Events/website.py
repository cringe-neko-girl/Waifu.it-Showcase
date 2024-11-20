import discord
from discord.ext import commands
import aiohttp_jinja2
import jinja2
from aiohttp import web
import socketio
import asyncio

class WebEventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sio = socketio.AsyncServer()
        self.app = web.Application()
        self.setup_routes()
        self.sio.attach(self.app)

    def setup_routes(self):
        """Set up routes for aiohttp."""
        # Set up Jinja2 template rendering
        aiohttp_jinja2.setup(self.app, loader=jinja2.FileSystemLoader('templates'))
        
        # Define routes
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/ws', self.websocket_handler)

    @commands.Cog.listener()
    async def on_ready(self):
        """Event triggered when the bot is ready."""
        print(f"Bot has logged in as {self.bot.user}")
        # Notify the web dashboard of the bot's status
        await self.sio.emit('status', {'status': 'Online'})
        await self.sio.emit('bot_info', {
            'username': self.bot.user.name,
            'status': 'Online',
            'activity': str(self.bot.activity)
        })

    @commands.Cog.listener()
    async def on_message(self, message):
        """Event triggered when a message is received."""
        # Send message data to the web dashboard
        if message.author != self.bot.user:
            await self.sio.emit('new_message', {
                'author': message.author.name,
                'content': message.content
            })

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Event triggered when a new member joins."""
        # Notify the web dashboard when a member joins
        await self.sio.emit('member_join', {'username': member.name})

    async def start_http_server(self):
        """Start the HTTP server that serves the templates."""
        runner = web.AppRunner(self.app)
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

        # WebSocket handling logic goes here
        try:
            while True:
                msg = await ws.receive_json()
                print(msg)  # Handle incoming WebSocket messages
        except:
            pass  # Handle disconnections or errors
        finally:
            print("WebSocket closed.")
        
        return ws

    @commands.command(name='start', hidden=True)
    async def start_http(self, ctx):
        """Start the HTTP server from a command."""
        await self.start_http_server()
        await ctx.send("HTTP server has started!")

# Setup function to add the cog to the bot
def setup(bot):
    bot.add_cog(WebEventCog(bot))
