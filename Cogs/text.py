import discord
from discord.ext import commands
import aiohttp
import os

class Texts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.access_token = os.getenv('Waifu_Token')

    async def fetch_fact(self):
        """Fetch a random fact from the waifu.it API."""
        url = "https://waifu.it/api/v4/fact"
        headers = {"Authorization": self.access_token}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    fact_text = data.get('fact', 'No fact found.')
                    return fact_text, data['_id']
                else:
                    return "Request failed", None

    async def fetch_quote(self):
        """Fetch a random quote from the waifu.it API."""
        url = "https://waifu.it/api/v4/quote"
        headers = {"Authorization": self.access_token}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    quote_text = data.get('quote', 'No quote found.')
                    return quote_text, data['_id']
                else:
                    return "Request failed", None

    @commands.command(name='fact')
    async def fact(self, ctx):
        fact_text, fact_id = await self.fetch_fact()

        # Create an embed with the fact
        embed = discord.Embed(
            title="Random Anime Fact",
            description=f"```{fact_text}```",
            color=discord.Color.random()
        )
        embed.set_footer(text=f"ID: {fact_id}\t\tPowered by waifu.it")

        # Add a button to fetch a new fact
        button = discord.ui.Button(emoji='🔀', style=discord.ButtonStyle.primary, custom_id='random_fact')

        view = discord.ui.View()
        view.add_item(button)

        await ctx.reply(embed=embed, view=view, mention_author=False)

    @commands.command(name='quote')
    async def quote(self, ctx):
        quote_text, quote_id = await self.fetch_quote()

        # Create an embed with the quote
        embed = discord.Embed(
            title="Anime Quote",
            description=f"```{quote_text}```",
            color=discord.Color.random()
        )
        embed.set_footer(text=f"ID: {quote_id}\nPowered by waifu.it", icon_url=self.bot.user.avatar)

        # Add a button to fetch a new quote
        button = discord.ui.Button(emoji='🔀', style=discord.ButtonStyle.primary, custom_id='random_quote')

        view = discord.ui.View()
        view.add_item(button)

        await ctx.reply(embed=embed, view=view, mention_author=False)

    @discord.ui.button(emoji='🔀', style=discord.ButtonStyle.primary, custom_id='random_fact')
    async def random_fact_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles button click to update the fact embed."""
        fact_text, fact_id = await self.fetch_fact()
        embed = discord.Embed(
            title="Random Anime Fact",
            description=f"```{fact_text}```",
            color=discord.Color.random()
        )
        embed.set_footer(text=f"ID: {fact_id}\t\tPowered by waifu.it")

        # Update the message with a new fact
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(emoji='🔀', style=discord.ButtonStyle.primary, custom_id='random_quote')
    async def random_quote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles button click to update the quote embed."""
        quote_text, quote_id = await self.fetch_quote()
        embed = discord.Embed(
            title="Anime Quote",
            description=f"```{quote_text}```",
            color=discord.Color.random()
        )
        embed.set_footer(text=f"ID: {quote_id}\nPowered by waifu.it", icon_url=self.bot.user.avatar)

        # Update the message with a new quote
        await interaction.response.edit_message(embed=embed)

    async def owoify_text(self, ctx, mode: str, text: str):
        """Helper function to interact with the waifu.it API."""
        url = f"https://waifu.it/api/v4/{mode}"
        params = {"text": text}
        headers = {"Authorization": self.access_token}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # Create an embed with the result
                    embed = discord.Embed(
                        title=f"{mode.capitalize()} Result",
                        description=data.get("text", "No text returned.")
                    )
                    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)

                    await ctx.reply(embed=embed, mention_author=False)
                else:
                    await ctx.send(f"Failed to {mode} the text. Please try again later.")
    
    @commands.command(name='owoify')
    async def owoify(self, ctx, *, text: str = "Hello world"):
        """Owoifies the provided text."""
        await self.owoify_text(ctx, "owoify", text)

    @commands.command(name='uvuify')
    async def uvuify(self, ctx, *, text: str = "Hello world"):
        """Uvuifies the provided text."""
        await self.owoify_text(ctx, "uvuify", text)

    @commands.command(name='uwuify')
    async def uwuify(self, ctx, *, text: str = "Hello world"):
        """Uwuifies the provided text."""
        await self.owoify_text(ctx, "uwuify", text)

# Example setup for adding the Cog to the bot
def setup(bot):
    bot.add_cog(Texts(bot))
