import os
import logging
import aiohttp
import discord
from discord.ext import commands
from discord.ui import Button, View
import random  # To randomly select an expression

class ResponseTemplate:
    def __init__(self, ):
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



        self.responses = {
            "angry": "{user} is angry at {target}!",
            "baka": "{user} calls {target} a baka!",
            "bite": "{user} bites {target} playfully.",
            "blush": "{user} blushes at {target}!",
            "bonk": "{user} bonks {target} on the head!",
            "bored": "{user} is bored.",
            "bully": "{user} bullies {target}!",
            "bye": "{user} says bye to {target}!",
            "chase": "{user} chases {target} around.",
            "cheer": "{user} cheers for {target}!",
            "cringe": "{user} feels the cringe for {target}.",
            "cry": "{user} cries for {target}.",
            "cuddle": "{user} cuddles with {target}.",
            "dab": "{user} does a dab.",
            "dance": "{user} dances energetically.",
            "die": "{user} falls dramatically.",
            "disgust": "{user} looks disgusted at {target}.",
            "facepalm": "{user} facepalms at {target}.",
            "feed": "{user} feeds {target}.",
            "glomp": "{user} glomps {target}.",
            "happy": "{user} feels happy!",
            "hi": "{user} says hi!",
            "highfive": "{user} high-fives {target}!",
            "hold": "{user} holds {target}.",
            "hug": "{user} hugs {target}.",
            "kick": "{user} kicks {target}.",
            "kill": "{user} plays a dramatic 'kill' role.",
            "kiss": "{user} gives {target} a kiss.",
            "laugh": "{user} laughs with {target}.",
            "lick": "{user} licks {target}.",
            "love": "{user} loves {target}.",
            "lurk": "{user} lurks around.",
            "midfing": "{user} shows a middle finger.",
            "nervous": "{user} feels nervous.",
            "nom": "{user} noms at {target}.",
            "nope": "{user} says nope to {target}.",
            "nuzzle": "{user} nuzzles {target}.",
            "panic": "{user} panics.",
            "pat": "{user} pats {target}.",
            "poke": "{user} pokes {target}.",
            "pout": "{user} pouts at {target}.",
            "punch": "{user} punches {target}.",
            "run": "{user} runs away from {target}.",
            "sad": "{user} feels sad.",
            "shoot": "{user} shoots an arrow at {target}.",
            "shrug": "{user} shrugs.",
            "sip": "{user} takes a sip.",
            "slap": "{user} slaps {target}.",
            "sleepy": "{user} feels sleepy.",
            "smile": "{user} smiles at {target}.",
            "smug": "{user} gives a smug smile.",
            "stab": "{user} stabs {target} playfully.",
            "stare": "{user} stares at {target}.",
            "suicide": "{user} talks about ending things dramatically.",
            "tease": "{user} teases {target}.",
            "think": "{user} thinks deeply.",
            "thumbsup": "{user} gives a thumbs up.",
            "tickle": "{user} tickles {target}.",
            "triggered": "{user} feels triggered by {target}.",
            "wag": "{user} wags their tail.",
            "wave": "{user} waves at {target}.",
            "wink": "{user} winks at {target}.",
            "yes": "{user} says yes!"
        }
    async def fetch_expression(self, expression):
        url = self.api_url.format(expression=expression)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"Authorization": self.access_token}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
                
    async def create_embed(self, expression, user, target):
        # Get the response text for the expression
        response = self.responses.get(expression, "No response found for this expression.")
        
        # Set the content based on whether the target is 'themselves'
        if target != "themselves":
            content = response.format(user=user.name, target=target.name if target else "someone")
        else:
            content = response.format(user=user.name, target="themselves")

        # Get the image URL from the API
        image_url = await self.get_image_url(expression)

        # Create the embed
        embed = discord.Embed(
            title=f"{content}",
            color=discord.Color.blue()
        )
        
        # If an image URL is returned, set it as the thumbnail
        if image_url:
            embed.set_image(url=image_url)

        return embed

    async def get_image_url(self, expression):
        try:
            # Define your API token here
            api_token = os.getenv('Waifu_Token')  # Replace with your actual token
            url = f'https://waifu.it/api/v4/{expression}'
            
            # Send an asynchronous GET request with the Authorization header
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={
                    'Authorization': api_token
                }) as response:
                    data = await response.json()

            # Extract the image URL from the response
            image_url = data.get('url')
            return image_url
        except Exception as e:
            print(f"Error fetching image for {expression}: {e}")
            return None
    
    async def create_embed_button(self, expression, user, image_url):
     data = await self.fetch_expression(expression)
     if not data or 'url' not in data:
        return None, None  # Return None for both if data isn't valid

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
      try:
        # Only defer if it hasn't been responded to already
        if not interaction.response.is_done():
            await interaction.response.defer()

        # Fetch the new expression data
        data = await self.fetch_expression(expression)
        image_url = data.get("url")
        
        # Create the new embed and button view
        embed, button_view = await self.create_embed_button(expression, user, image_url)
        
        # Update the message with the new embed and view
        await interaction.response.edit_message(embed=embed, view=button_view)

      except discord.errors.NotFound:
        # Handle the case where the interaction is no longer valid (timed out or unknown)
        print("Interaction not found or expired.")
      except Exception as e:
        # General error handling
        print(f"An error occurred: {e}")


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
        return None, None  # Return None for both if data isn't valid

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
            async def command(ctx, user: discord.User = None, target: discord.User = None, expression=expression):
                """Send an embed with the corresponding expression."""
                if not user:
                    user = ctx.author
                if not target:
                    target = "themselves"

                if user and target:
                    user = ctx.author
                    target = target


                    
                
                embed = await ResponseTemplate().create_embed(expression, user, target)
                image_url = embed.image.url if embed.image else None


                await ctx.reply(embed=embed, mention_author=False, view=More_Info(expression, user, image_url))

                
            # Register the command to the bot
            command.__name__ = expression  # Ensure the function name is set
            self.bot.add_command(command)

class More_Info(View):
    def __init__(self, expression, user, image_url):
        super().__init__(timeout=None)
        self.expression = expression
        self.user = user
        self.image_url = image_url

    @discord.ui.button(label="More Information", style=discord.ButtonStyle.gray)
    async def more_info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed, button_view = await ResponseTemplate().create_embed_button(self.expression, self.user, self.image_url)
        await interaction.response.send_message(embed=embed, view=button_view, ephemeral=True)  # Send the message as ephemeral


# Setup function for the bot
def setup(bot):
    bot.add_cog(Interactions(bot))
