import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import logging
from collections import defaultdict

from keep_alive import keep_alive
from commands.soundboard import setup_soundboard_command
from commands.sounds import setup_sounds_commands
from commands.create_combination import setup_create_combination_command
from commands.list_combinations import setup_list_combinations_command
from commands.play_combinations import setup_play_created_combinations_command
from commands.delete_combinations import setup_delete_combinations_command

sound_queues = defaultdict(list)
queue_locks  = defaultdict(asyncio.Lock)

# Load environment variables
load_dotenv()

keep_alive() 
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot setup
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Register all commands
setup_soundboard_command(bot, sound_queues, queue_locks)
setup_sounds_commands(bot)
setup_create_combination_command(bot, sound_queues, queue_locks)
setup_list_combinations_command(bot)
setup_play_created_combinations_command(bot)
setup_delete_combinations_command(bot)

@bot.event
async def on_ready():
    logger.info(f"{bot.user} has connected to Discord!")
    try:
        await bot.tree.sync()
        logger.info(f"Synced command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")


# ============= Run the bot =============
def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError(
            "DISCORD_TOKEN not found in .env file. "
            "Please add your bot token to the .env file."
        )
    
    bot.run(token)

@bot.tree.command(name="sync", description="Sync commands for this server")
async def sync(interaction: discord.Interaction):
    await interaction.response.send_message("Syncing commands...", ephemeral=True)
    try:
        await bot.tree.sync()
        await interaction.followup.send("Commands synced successfully!", ephemeral=True)
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
        await interaction.followup.send("Failed to sync commands.", ephemeral=True)

if __name__ == "__main__":
    main()
