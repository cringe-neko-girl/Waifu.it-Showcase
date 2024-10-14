import discord
from discord.ext import commands
import aiohttp
import random
import os

class Texts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.access_token = os.getenv('Waifu_Token')


    @commands.command(name='fact')
    async def fact(self, ctx):
        url = "https://waifu.it/api/v4/fact"
        headers = {
            "Authorization": self.access_token
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    fact_text = data.get('fact', 'No fact found.')

                    # Create an embed with the fact
                    embed = discord.Embed(
                        title="Random Anime Fact",
                        description=f"```{fact_text}```",
                        color=discord.Color.random()

                    )
                    embed.set_footer(text=f"ID: {data['_id']}\t\tPowered by waifu.it")

                    await ctx.reply(embed=embed, mention_author=False)
                else:
                    await ctx.send(f"Request failed with status: {response.status}", mention_author=False)

        
    @commands.command(name='password')
    async def password(self, ctx, length: int = 12):
        url = "https://waifu.it/api/v4/password"
        headers = {
            "Authorization": self.access_token
        }
        params = {
            "charLength": length
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    password = data.get('password', 'No password found.')
                    await ctx.send(f"Generated Password: `{password}`")
                else:
                    await ctx.send(f"Request failed with status: {response.status}")

 

    @commands.command(name='quote')
    async def quote(self, ctx):
        url = "https://waifu.it/api/v4/quote"
        headers = {
            "Authorization": self.access_token
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    quote_text = data.get('quote', 'No quote found.')

                    # Create an embed with the fact
                    embed = discord.Embed(
                        title="Anume Quote",
                        description=f"```{quote_text}```",
                        color=discord.Color.random()

                    )
                    embed.set_footer(text=f"ID: {data['_id']}\nPowered by waifu.it", icon_url=self.bot.user.avatar)

                    await ctx.reply(embed=embed, mention_author=False)
                else:
                    await ctx.send(f"Request failed with status: {response.status}", mention_author=False)

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
