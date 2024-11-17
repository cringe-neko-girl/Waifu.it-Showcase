import json
import os
import logging
import discord
from discord.ext import commands

# Define ANSI escape codes for colors
class LogColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'

# Set up logging with custom formatting
class CustomFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.DEBUG:
            record.msg = f"{LogColors.OKBLUE}{record.msg}{LogColors.ENDC}"
        elif record.levelno == logging.INFO:
            record.msg = f"{LogColors.OKGREEN}{record.msg}{LogColors.ENDC}"
        elif record.levelno == logging.WARNING:
            record.msg = f"{LogColors.WARNING}{record.msg}{LogColors.ENDC}"
        elif record.levelno == logging.ERROR:
            record.msg = f"{LogColors.ERROR}{record.msg}{LogColors.ENDC}"
        return super().format(record)

# Help class to manage command help system
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_data = _Help()
        self.command_mapping_file = 'Data/commands/help/command_map.json'
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.command_mapping_file), exist_ok=True)
        if not os.path.exists(self.command_mapping_file):
            self._save_command_mapping({})

    def _load_command_mapping(self):
        """Load the command mapping from a JSON file."""
        self._ensure_file_exists()
        try:
            with open(self.command_mapping_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error loading command mapping: {e}")
            return {}

    def _get_cog_commands(self):
        """Return commands for each cog, excluding hidden commands."""
        return {
            cog_name: [cmd.name for cmd in cog.get_commands() if not cmd.hidden]
            for cog_name, cog in self.bot.cogs.items() if cog
        }

    def _save_command_mapping(self, mapping):
        """Save command mapping to a JSON file."""
        with open(self.command_mapping_file, 'w') as f:
            json.dump(mapping, f, indent=4)

    @commands.command(hidden=True)
    async def help(self, ctx, command_name: str = None):
        command_mapping = self._load_command_mapping()
        cog_commands = self._get_cog_commands()

        if command_name:
            for cog_name, commands_list in cog_commands.items():
                if command_name in commands_list:
                    embed = discord.Embed(title=self.help_data.title, description=self.help_data.description)
                    embed.add_field(name=cog_name, value=f'`{command_name}`', inline=False)

                    # Fetch command details from the saved JSON
                    cmd_details = command_mapping.get(cog_name, {}).get(command_name, 'No details available')
                    embed.add_field(name="Command Details", value=f"`{cmd_details}`", inline=False)

                    await ctx.send(embed=embed)
                    return

            await ctx.send(f"No command named `{command_name}` found.")
        else:
            """Lists all available commands."""
            embed = discord.Embed(title=self.help_data.title, description=self.help_data.description)

            # Create categories for commands
            images_commands = []
            texts_commands = []
            interactions_commands = []

            # Loop through each cog to categorize commands
            for cog_name, commands_list in cog_commands.items():
                visible_commands_cog = [cmd for cmd in commands_list if not self.bot.get_command(cmd).hidden]
                if visible_commands_cog:
                    # Assign commands to the respective categories based on cog names
                    if 'Images' in cog_name:
                        images_commands.extend(visible_commands_cog)
                    elif 'Texts' in cog_name:
                        texts_commands.extend(visible_commands_cog)
                    elif 'Interactions' in cog_name:
                        interactions_commands.extend(visible_commands_cog)

            # Add commands from each category to the embed
            if images_commands:
                embed.add_field(name="Images", value='\t'.join([f"`{cmd}`" for cmd in images_commands]), inline=False)
            if texts_commands:
                embed.add_field(name="Texts", value='\t'.join([f"`{cmd}`" for cmd in texts_commands]), inline=False)
            if interactions_commands:
                embed.add_field(name="Interactions", value='\t'.join([f"`{cmd}`" for cmd in interactions_commands]), inline=False)

            # Get visible commands for the main bot (not in a specific cog)
            ignored_commands = {"fact", "password", "quote", "owoify", "uvuify", "uwuify", 'waifu', 'husbando'}
            visible_commands = [cmd.name for cmd in self.bot.commands if not cmd.hidden and cmd.name not in ignored_commands]
            if visible_commands:
                command_string = '\t'.join([f"`{cmd}`" for cmd in visible_commands])

                # Split long command strings into chunks that fit Discord's embed limit
                while len(command_string) > 1024:
                    split_index = command_string.rfind('\t', 0, 1024)
                    if split_index == -1:
                        split_index = 1024  # Fallback to 1024 if no tab found

                    embed.add_field(name="", value=command_string[:split_index], inline=False)
                    command_string = command_string[split_index + 1:]  # Remove added chunk

                # Add the remaining commands if any
                if command_string:
                    embed.add_field(name="Interactions", value=command_string, inline=False)

            # Ensure the embed is not empty
            if embed.fields:
                embed.set_thumbnail(url=self.help_data.set_thumbnail)
                embed.set_image(url=self.help_data.set_image)
                await ctx.reply(embed=embed, mention_author=False)
            else:
                await ctx.send("No available commands found.")

# Help data structure for displaying information
class _Help:
    def __init__(self):
        self.title = "Help | Command List"
        self.description = ":heart: `Waifu.it | Showcase` showcases the capabilities of the Waifu.it API, acting as a bridge and offering direct links to resources that are publicly available through our API.\n- Get started at [waifu.it](https://waifu.it)."
        self.set_image = "https://i.pinimg.com/564x/78/f3/bc/78f3bcc7b97d5d1c8b30bc12d76f326f.jpg"
        self.set_thumbnail = 'https://avatars.githubusercontent.com/u/79479798?s=200&v=4'

# Setup function for the bot
def setup(bot):
    bot.add_cog(Help(bot))
