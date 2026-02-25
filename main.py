import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import logging
from collections import defaultdict
from pathlib import Path

from keep_alive import keep_alive

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

bot = commands.Bot(command_prefix="/", intents=intents)

# Attach shared data to bot for access in cogs
bot.sound_queues = sound_queues
bot.queue_locks = queue_locks

async def load_cogs():
    """Load all cogs from the commands directory"""
    cogs_dir = Path("commands")
    for cog_file in cogs_dir.glob("*.py"):
        if cog_file.name.startswith("_") or cog_file.name == "utils.py":
            continue
        cog_name = cog_file.stem
        try:
            await bot.load_extension(f"commands.{cog_name}")
            logger.info(f"Loaded cog: {cog_name}")
        except Exception as e:
            logger.error(f"Failed to load cog {cog_name}: {e}")

@bot.event
async def on_ready():
    logger.info(f"{bot.user} has connected to Discord!")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")


# ============= Run the bot =============
async def main():
    async with bot:
        await load_cogs()
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError(
                "DISCORD_TOKEN not found in .env file. "
                "Please add your bot token to the .env file."
            )
        await bot.start(token)

asyncio.run(main())
