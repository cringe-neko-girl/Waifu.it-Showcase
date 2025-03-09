import os
import logging
import aiohttp
import discord
from discord.ext import commands


class View(discord.ui.View):
    def __init__(self, ctx, waifu_data, api_url, items_per_page=1, items_per_section=5):
        super().__init__()
        self.ctx = ctx
        
        if isinstance(waifu_data, list):
            self.waifu_data = waifu_data
        else:
            print("Invalid waifu_data structure:", waifu_data)
            self.waifu_data = []

        self.items_per_page = items_per_page
        self.items_per_section = items_per_section
        self.page_index = 0
        self.section_index = 0
        
        self.paginated_data = self.paginate_json(self.waifu_data, items_per_section)
        self.total_sections = len(self.paginated_data)
        self.total_pages = (self.total_sections + items_per_page - 1) // items_per_page
        self.api_url = api_url
        self.access_token = os.getenv('Waifu_Token')
        
        if self.total_sections < 2:
            self.disable_buttons()

    def disable_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.custom_id in ['previous_button', 'next_button']:
                item.disabled = True
                self.remove_item(item)

    def paginate_json(self, data, page_size):
        pages = [data[i:i + page_size] for i in range(0, len(data), page_size)]
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
            anime_names = item.get('name', {})
            anime_images = [item.get('image', {}).get('large')]
            anime_description = item.get('description', "No description available.")
            media_nodes = item.get('media', {}).get('nodes', [{}])
            anime_type = media_nodes[0].get('type', 'Unknown') if media_nodes else 'Unknown'
            anime_format = media_nodes[0].get('format', 'Unknown') if media_nodes else 'Unknown'
            banner_image_url = media_nodes[0].get('bannerImage')
            
            embed = discord.Embed(
                title=anime_names.get('full', "Unknown"),
                description=anime_description,
                color=0x99ccff,
                url="https://rajtech.me"
            )
  
            if banner_image_url:
                banner_embed = discord.Embed(
                    title=anime_names.get('full', "Unknown"),
                    description=anime_description,
                    color=0x99ccff,
                    url="https://rajtech.me"
                )
                banner_embed.set_image(url=banner_image_url)
                embeds.append(banner_embed)

            image_embed = discord.Embed(
                title=anime_names.get('full', "Unknown"),
                description=anime_description,
                url="https://rajtech.me"
            )
            image_embed.set_image(url=anime_images[0])
            embeds.append(image_embed)
            
            user = self.ctx.author
            avatar_url = user.avatar.url if user.avatar else None
            
            for embed in embeds:
                embed.set_footer(text=f"Requested by {user}", icon_url=avatar_url)

        return embeds
    
    @discord.ui.button(emoji='🔀', style=discord.ButtonStyle.primary)
    async def random(self, button: discord.ui.Button, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url, headers={"Authorization": self.access_token}) as response:
                if response.status != 200:
                    await interaction.response.send_message(f"Failed to fetch waifu data. Status code: {response.status}", ephemeral=True)
                    return

                data = await response.json()
                embeds = self.extract_data_and_create_embeds(data)
                await button.response.edit_message(embeds=embeds, view=self)

    def extract_data_and_create_embeds(self, data):
        embeds = []
        anime_names = data.get('name', {})
        anime_titles = [anime["title"]["romaji"] for anime in data.get("media", {}).get("nodes", [])]
        anime_images = [data.get('image', {}).get('large')]
        anime_description = data.get('description', "No description available.")
        media_nodes = data.get('media', {}).get('nodes', [{}])
        anime_type = media_nodes[0].get('type', 'Unknown') if media_nodes else 'Unknown'
        banner_image_url = media_nodes[0].get('bannerImage')
        anime_popularity = data.get('media', {}).get('nodes', [{}])[0].get('popularity', 0)
        
        max_popularity = 105000
        score_percentage = min(anime_popularity / max_popularity, 1.0)
        popularity_bar = f"{'▰' * int(score_percentage * 10)}{'▱' * (10 - int(score_percentage * 10))}"

        footer_text = (
            f"Titles: {', '.join(anime_titles) if anime_titles else 'Unknown'}\n"
            f"Type: {anime_type.title()}\n\n"
            f"Popularity: {anime_popularity}\n{popularity_bar}"
        )

        main_embed = discord.Embed(
            title=anime_names.get('full', "Unknown"),
            description=anime_description,
            color=0x99ccff,
            url="https://rajtech.me"
        )
        main_embed.set_footer(text=footer_text)
        embeds.append(main_embed)

        if anime_images[0]:
            image_embed = discord.Embed(
                title=anime_names.get('full', "Unknown"),
                description=anime_description,
                url="https://rajtech.me"
            )
            image_embed.set_image(url=anime_images[0])
            image_embed.set_footer(text=footer_text)
            embeds.append(image_embed)

        if banner_image_url:
            banner_embed = discord.Embed(
                title=anime_names.get('full', "Unknown"),
                description=anime_description,
                color=0x99ccff,
                url="https://rajtech.me"
            )
            banner_embed.set_image(url=banner_image_url)
            banner_embed.set_footer(text=footer_text)
            embeds.append(banner_embed)

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


    async def create_embed(self, ctx, data, is_waifu=True):
     embeds = []

     # Extract necessary information
     anime_names = data.get('name', {})
     anime_images = [data.get('image', {}).get('large')]
     anime_description = data.get('description', "No description available.")
     media_nodes = data.get('media', {}).get('nodes', [{}])
     anime_type = media_nodes[0].get('type', 'Unknown') if media_nodes else 'Unknown'
     anime_format = media_nodes[0].get('format', 'Unknown') if media_nodes else 'Unknown'
     banner_image_url = media_nodes[0].get('bannerImage')
     anime_popularity = data.get('media', {}).get('nodes', [{}])[0].get('popularity', 0)
     anime_titles = [node['title']['userPreferred'] for node in data['media']['nodes'] if node['type'] == 'ANIME']
     anime_type = media_nodes[0].get('type', 'Unknown') if media_nodes else 'Unknown'



     # Create popularity bar
     max_popularity = 105000  # Adjust this value to a realistic maximum popularity
     score_percentage = min(anime_popularity / max_popularity, 1.0)  # Ensure the percentage doesn't exceed 1
     popularity_bar = f"{'▰' * int(score_percentage * 10)}{'▱' * (10 - int(score_percentage * 10))}"
    
     # Create an embed for the main image
     image_embed = discord.Embed(
        title=anime_names.get('full', "Unknown"),
        description=anime_description,
        color=0x99ccff,
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

     # Set footer with user info and popularity score
     user = ctx.author  # or interaction.user if you want to use interaction
     avatar_url = user.avatar.url if user.avatar else None

     footer_text = (
        f"Source: {anime_titles} \t"
        f"•  Type: {anime_type.title()} \n"
        f"Popularity: {anime_popularity}\n{popularity_bar}"
     )

     for embed in embeds:
        embed.set_footer(text=footer_text, icon_url=avatar_url)

     return embeds 
  
    @commands.command(name='waifu', help='Fetch a random waifu image from the Waifu.it API.')
    async def waifu(self, ctx, num_images=10):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url_waifu, headers={"Authorization": self.access_token}) as response:
                if response.status != 200:
                    await ctx.send(f"Failed to fetch waifu data. Status code: {response.status}")
                    return

                data = await response.json()

        embeds = await self.create_embed(ctx,data, is_waifu=True)

        # Send the embed with buttons
        view = View(ctx, data, self.api_url_waifu)
        await ctx.reply(embeds=embeds, view=view, mention_author=False)

    @commands.command(name='husbando', help='Fetch a random husbando image from the Waifu.it API.')
    async def husbando(self, ctx, num_images=10):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url_husbando, headers={"Authorization": self.access_token}) as response:
                if response.status != 200:
                    await ctx.send(f"Failed to fetch husbando data. Status code: {response.status}")
                    return

                data = await response.json()

        embeds = await self.create_embed(ctx ,data, is_waifu=False)

        # Send the embed with buttons
        view = View(ctx, data, self.api_url_husbando)
        await ctx.reply(embeds=embeds, view=view, mention_author=False)


def setup(bot):
    bot.add_cog(Images(bot))
