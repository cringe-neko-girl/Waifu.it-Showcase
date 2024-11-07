import os
import logging
import aiohttp
import discord
from discord.ext import commands
from discord.ui import Button, View
import random  # To randomly select an expression

class Interactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://waifu.it/api/v4/{expression}"
        self.access_token = os.getenv('Waifu_Token')

        self.set_thumbnail = 'https://avatars.githubusercontent.com/u/79479798?s=200&v=4'

        # Code snippets for Python and JavaScript
        self.python_example = (
            "```python\n"
            "import requests\n\n"
            "# Replace 'Your-API-Token' with the token you got from the Kohai Bot\n"
            "url = 'https://waifu.it/api/v4/{expression}'\n"
            "response = requests.get(url, headers={\n"
            "  'Authorization': 'Your-API-Token'\n"
            "})\n"
            "data = response.json()\n\n"
            "print(data)\n"
            "```"
        )

        self.js_example = (
            "```javascript\n"
            "import axios from 'axios';\n\n"
            "// Replace 'Your-API-Token' with the token you got from the Kohai Bot\n"
            "const url = 'https://waifu.it/api/v4/{expression}';\n"
            "const fetchData = async () => {\n"
            "  try {\n"
            "    const { data } = await axios.get(url, {\n"
            "      headers: {\n"
            "        Authorization: 'Your-API-Token'\n"
            "      }\n"
            "    });\n"
            "    return data;\n"
            "  } catch (err) {\n"
            "    throw new Error(err.message);\n"
            "  }\n"
            "};\n\n"
            "fetchData().then(data => console.log(data));\n"
            "```"
        )

        # Create commands when the cog is loaded
        self.create_hardcoded_commands()

    async def fetch_expression(self, expression):
        url = self.api_url.format(expression=expression)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"Authorization": self.access_token}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None

    async def create_embed(self, expression, user=None):
        data = await self.fetch_expression(expression)
        if not data or 'url' not in data:
            return None

        title = f"{expression.capitalize()} Expression"
        if user:
            title = f"{user.display_name} {title}"

        description = (
            f"The `/{expression}` endpoint allows users to receive appropriate anime responses from the server. "
            f"This document provides a detailed description of the endpoint, including input headers, response "
            f"examples, and code snippets for handling the requests."
        )

        embed = discord.Embed(
            title=title,
            description=description,
        )
        image_url = data.get("url")
        if image_url:
            embed.set_image(url=image_url)

        embed.set_thumbnail(url=self.set_thumbnail)

        # Create buttons for examples
        button_view = View(timeout=None)
        python_button = Button(label="Python Example", style=discord.ButtonStyle.primary)
        js_button = Button(label="JavaScript Example", style=discord.ButtonStyle.primary)

        # Random button
        random_button = Button(emoji="🔀", style=discord.ButtonStyle.secondary)
        
        # Callback for the Random button (refreshes the same expression)
        async def random_button_callback(interaction):
            embed, button_view = await self.create_embed(expression, user)
            await interaction.response.edit_message(embed=embed, view=button_view)  # Update the message with the same embed

        async def python_example_callback(interaction):
            await interaction.response.send_message(
                self.python_example.replace('{expression}', expression), ephemeral=True
            )

        async def js_example_callback(interaction):
            await interaction.response.send_message(
                self.js_example.replace('{expression}', expression), ephemeral=True
            )

        python_button.callback = python_example_callback
        js_button.callback = js_example_callback
        random_button.callback = random_button_callback

        button_view.add_item(python_button)
        button_view.add_item(js_button)
        button_view.add_item(random_button)  # Add the random button to the view

        return embed, button_view

    def create_hardcoded_commands(self):
        expressions = [
            "angry", "baka", "bite", "blush", "bonk", "bored", "bully", "bye",
            "chase", "cheer", "cringe", "cry", "cuddle", "dab", "dance", "die",
            "disgust", "facepalm", "feed", "glomp", "happy", "hi", "highfive",
            "hold", "hug", "kick", "kill", "kiss", "laugh", "lick", "love",
            "lurk", "midfing", "nervous", "nom", "nope", "nuzzle", "panic",
            "pat", "poke", "pout", "punch", "run", "sad", "shoot", "shrug",
            "sip", "slap", "sleepy", "smile", "smug", "stab", "stare", 
            "suicide", "tease", "think", "thumbsup", "tickle", "triggered",
            "wag", "wave", "wink", "yes"
        ]

        for expression in expressions:
            # Define a command for each expression
            @commands.command(name=expression)
            async def command(ctx, user: discord.User = None, expression=expression):
                """Send an embed with the corresponding expression."""
                embed, button_view = await self.create_embed(expression, user)
                if embed:
                    await ctx.reply(embed=embed, mention_author=False, view=button_view)
                else:
                    await ctx.reply(f"Could not fetch the expression: {expression}", mention_author=False)

            # Register the command to the bot
            command.__name__ = expression  # Ensure the function name is set
            self.bot.add_command(command)

# Setup function for the bot
def setup(bot):
    bot.add_cog(Interactions(bot))
