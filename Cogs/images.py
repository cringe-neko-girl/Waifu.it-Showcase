import os
import logging
import aiohttp
import discord
from discord.ext import commands


class View(discord.ui.View):
    def __init__(self, ctx, waifu_data, api_url, items_per_page=1, items_per_section=5):
        super().__init__()
        self.ctx = ctx
        
        # Check if waifu_data is a list; if not, raise an error or set to empty list
        if isinstance(waifu_data, list):
            self.waifu_data = waifu_data
        else:
            print("Invalid waifu_data structure:", waifu_data)  # Log invalid structure
            self.waifu_data = []  # or raise an exception

        self.items_per_page = items_per_page
        self.items_per_section = items_per_section
        self.page_index = 0
        self.section_index = 0
        
        # Paginate the data
        self.paginated_data = self.paginate_json(self.waifu_data, items_per_section)
        self.total_sections = len(self.paginated_data)
        self.total_pages = (self.total_sections + items_per_page - 1) // items_per_page
        self.api_url = api_url
        self.access_token = os.getenv('Waifu_Token')
        
        # Disable buttons if there are fewer than 2 sections
        if self.total_sections < 2:
            self.disable_buttons()

    def disable_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.custom_id in ['previous_button', 'next_button']:
                item.disabled = True
                self.remove_item(item)

    def paginate_json(self, data, page_size):
        """Paginate JSON data and return as a list of pages."""
        pages = []
        for i in range(0, len(data), page_size):
            pages.append(data[i:i + page_size])
        return pages

    async def update_message(self, interaction=None):
        if self.section_index >= self.total_sections:
            if interaction:
                await interaction.response.send_message("No more sections available.", ephemeral=True)
            return
        
        section_data = self.paginated_data[self.section_index]
        
        embeds = self.create_embeds(section_data)

        if interaction:
            await interaction.response.edit_message(embeds=embeds)
        else:
            await self.ctx.send(embeds=embeds)

    def create_embeds(self, section_data):
        embeds = []
        for item in section_data:
            # Extract necessary information
            anime_names = item.get('name', {})
            anime_images = [item.get('image', {}).get('large')]
            anime_description = item.get('description', "No description available.")
            media_nodes = item.get('media', {}).get('nodes', [{}])
            anime_type = media_nodes[0].get('type', 'Unknown') if media_nodes else 'Unknown'
            anime_format = media_nodes[0].get('format', 'Unknown') if media_nodes else 'Unknown'
            banner_image_url = media_nodes[0].get('bannerImage')
            
            # Create the main embed
            embed = discord.Embed(
                title=anime_names.get('full', "Unknown"),
                description=anime_description,
                color=0x99ccff,
                url="https://rajtech.me"
            )
            
            # Create an embed for the banner image if it exists
            if banner_image_url:
                banner_embed = discord.Embed(
                    title=anime_names.get('full', "Unknown"),
                    description=anime_description,
                    color=0x99ccff,
                    url="https://rajtech.me"
                )
                banner_embed.set_image(url=banner_image_url)
                embeds.append(banner_embed)  # Append banner embed

            # Create an embed for the main image
            image_embed = discord.Embed(
                title=anime_names.get('full', "Unknown"),
                description=anime_description,
                url="https://rajtech.me"
            )
            image_embed.set_image(url=anime_images[0])  # Set the main image
            embeds.append(image_embed)  # Append image embed
            
            # Set footer with user info
            user = self.ctx.author  # or interaction.user if you want to use interaction
            avatar_url = user.avatar.url if user.avatar else None
            
            for embed in embeds:
                embed.set_footer(text=f"Requested by {user}", icon_url=avatar_url)

        return embeds
    
    @discord.ui.button(emoji='🔀', style=discord.ButtonStyle.primary)
    async def random(self, button: discord.ui.Button, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:  # Create an aiohttp session
            async with session.get(self.api_url, headers={"Authorization": self.access_token}) as response:
                if response.status != 200:
                    await interaction.response.send_message(f"Failed to fetch waifu data. Status code: {response.status}", ephemeral=True)
                    return

                data = await response.json()  # Asynchronously read the response as JSON
                
                # Extract necessary information from the data
                embeds = self.extract_data_and_create_embeds(data)

                # Send the initial embed with buttons
                await button.response.edit_message(embeds=embeds, view=self)

    def extract_data_and_create_embeds(self, data):
        embeds = []
        
        anime_names = data.get('name', {})
        anime_images = [data.get('image', {}).get('large')]
        anime_description = data.get('description', "No description available.")
        media_nodes = data.get('media', {}).get('nodes', [{}])
        anime_type = media_nodes[0].get('type', 'Unknown') if media_nodes else 'Unknown'
        anime_format = media_nodes[0].get('format', 'Unknown') if media_nodes else 'Unknown'
        banner_image_url = media_nodes[0].get('bannerImage')

        # Create the main embed
        embed = discord.Embed(
            title=anime_names.get('full', "Unknown"),
            description=anime_description,
            color=0x99ccff,
            url="https://rajtech.me"
        )
        # Create an embed for the main image
        image_embed = discord.Embed(
            title=anime_names.get('full', "Unknown"),
            description=anime_description,
            url="https://rajtech.me"
        )
        image_embed.set_image(url=anime_images[0])  # Set the main image
        embeds.append(image_embed)  # Append image embed
        
        # Create an embed for the banner image if it exists
        if banner_image_url:
            banner_embed = discord.Embed(
                title=anime_names.get('full', "Unknown"),
                description=anime_description,
                color=0x99ccff,
                url="https://rajtech.me"
            )
            banner_embed.set_image(url=banner_image_url)
            embeds.append(banner_embed)  # Append banner embed

        

        return embeds

    @discord.ui.button(emoji='<:left_arrow:1290517571329724450>', style=discord.ButtonStyle.primary, custom_id='previous_button')
    async def previous_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.section_index > 0:
            self.section_index -= 1
            await self.update_message(interaction)
        else:
            await interaction.response.send_message("You are already at the first section.", ephemeral=True)

    @discord.ui.button(emoji='<:right_arrow:1290517494724956261>', style=discord.ButtonStyle.primary, custom_id='next_button')
    async def next_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.section_index < self.total_sections - 1:
            self.section_index += 1
            await self.update_message(interaction)
        else:
            await interaction.response.send_message("You are already at the last section.", ephemeral=True)
            
            
            
            
            
            
            
            
            
            
            
            
            
            
                    

class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url_waifu = "https://waifu.it/api/v4/waifu"
        self.api_url_husbando = "https://waifu.it/api/v4/husbando"
        self.access_token = os.getenv('Waifu_Token')

        if not self.access_token:
            logging.error("No access token found. Please set the Waifu_Token environment variable.")
            raise ValueError("No access token found.")

        logging.debug("Images Cog initialized with API URL: %s", self.api_url_husbando)
        
    @commands.command(name='waifu', help='Fetch a random waifu image from the Waifu.it API.')
    async def waifu(self, ctx, num_images=10):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url_waifu, headers={"Authorization": self.access_token}) as response:
                if response.status != 200:
                    await ctx.send(f"Failed to fetch waifu data. Status code: {response.status}")
                    return

                data = await response.json()

        # Extract necessary information from the data
        anime_names = data.get('name', {})
        anime_images = [data.get('image', {}).get('large')]
        anime_description = data.get('description', "No description available.")
        media_node = data.get('media', {}).get('nodes', [{}])[0]
        anime_type = media_node.get('type', 'Unknown')
        anime_format = media_node.get('format', 'Unknown')
        banner_image_url = media_node.get('bannerImage')

        anime_source_name = f"{anime_type} - {anime_format}"  # Adjust source name based on type and format

        # Create the initial embed
        embed = discord.Embed(title=f'{anime_names.get("userPreferred", "Unknown")}', description=anime_description)
        if banner_image_url:
            embed.set_image(url=banner_image_url)
            embed.set_thumbnail(url=anime_images[0])
        else:
            embed.set_image(url=anime_images[0])




        # Set the footer text based on type and format
        preferred_languages = ['romaji', 'native', 'english']  # Define your preferred languages here
        title = next((media_node.get('title', {}).get(lang) for lang in preferred_languages if media_node.get('title', {}).get(lang)), 'N/A')
        footer_text = (
            f"Type: {media_node.get('type').lower().title()}\n"
            f"Source: {title.lower().title()}"
        )
        embed.set_footer(text=footer_text)

        # Send the initial embed with buttons
        view = View(ctx, data, self.api_url_waifu)
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @commands.command(name='husbando', help='Fetch a random husbando image from the Waifu.it API.')
    async def husbando(self, ctx, num_images=10):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url_husbando, headers={"Authorization": self.access_token}) as response:
                if response.status != 200:
                    await ctx.send(f"Failed to fetch waifu data. Status code: {response.status}")
                    return

                data = await response.json()

        # Extract necessary information from the data
        anime_names = data.get('name', {})
        anime_images = [data.get('image', {}).get('large')]
        anime_description = data.get('description', "No description available.")
        media_node = data.get('media', {}).get('nodes', [{}])[0]
        anime_type = media_node.get('type', 'Unknown')
        anime_format = media_node.get('format', 'Unknown')
        banner_image_url = media_node.get('bannerImage')

        anime_source_name = f"{anime_type} - {anime_format}"  # Adjust source name based on type and format

        # Create the initial embed
        embed = discord.Embed(title=f'{anime_names.get("userPreferred", "Unknown")}', description=anime_description)
        if banner_image_url:
           embed.set_image(url=banner_image_url)
           embed.set_thumbnail(url=anime_images[0])
        else:
           embed.set_image(url=anime_images[0])


        # Set the footer text based on type and format
        preferred_languages = ['romaji', 'native', 'english']  # Define your preferred languages here
        title = next((media_node.get('title', {}).get(lang) for lang in preferred_languages if media_node.get('title', {}).get(lang)), 'N/A')
        footer_text = (
            f"Type: {media_node.get('type').lower().title()}\n"
            f"Source: {title.lower().title()}"
        )
        embed.set_footer(text=footer_text)

        # Send the initial embed with buttons
        view = View(ctx, data, self.api_url_husbando)
        await ctx.reply(embed=embed, view=view, mention_author=False)

def setup(bot):
    bot.add_cog(Images(bot))
