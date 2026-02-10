import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import logging

from collections import defaultdict

sound_queues = defaultdict(list)
queue_locks  = defaultdict(asyncio.Lock)

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot setup
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Store available soundboard sounds
available_sounds = {}


async def load_sounds(guild: discord.Guild):
    """Load all soundboard sounds from the guild"""
    global available_sounds
    available_sounds = {}
    
    try:
        # Get soundboard sounds from the guild
        soundboard_sounds = await guild.fetch_soundboard_sounds()
        
        if not soundboard_sounds:
            logger.warning(f"No soundboard sounds found for guild {guild.name}")
            return False
        
        # Store soundboard sounds by name
        for sound in soundboard_sounds:
            available_sounds[sound.name] = sound
            logger.info(f"Loaded soundboard sound: {sound.name}")
        
        logger.info(f"Loaded {len(available_sounds)} soundboard sounds")
        return True
    
    except Exception as e:
        logger.error(f"Error loading soundboard sounds: {e}")
        return False


class SoundboardView(discord.ui.View):
    """View with buttons for selecting sounds"""
    
    def __init__(self):
        super().__init__(timeout=None)
        self.add_sound_buttons()
        self.add_item(self.create_play_queue_button())

    def add_sound_buttons(self):
        for sound_name in list(available_sounds.keys())[:20]:  # leave space for Play button
            button = discord.ui.Button(
                label=sound_name[:80],
                style=discord.ButtonStyle.primary
            )
            button.callback = self.make_add_to_queue_callback(sound_name)
            self.add_item(button)

    def create_play_queue_button(self):
        button = discord.ui.Button(
            label="▶️ Play Queue",
            style=discord.ButtonStyle.green,
            row=4  # bottom row
        )
        button.callback = self.play_queue_callback
        return button

    def make_add_to_queue_callback(self, sound_name: str):
        async def callback(interaction: discord.Interaction):
            await self.add_to_queue(interaction, sound_name)
        return callback

    async def add_to_queue(self, interaction: discord.Interaction, sound_name: str):
        if sound_name not in available_sounds:
            await interaction.response.send_message("Sound not found.", ephemeral=True)
            return

        guild = interaction.guild
        async with queue_locks[guild.id]:
            sound_queues[guild.id].append(available_sounds[sound_name])

        count = len(sound_queues[guild.id])
        await interaction.response.send_message(
            f"**{sound_name}** added to queue → position **{count}**\n"
            f"Queue size: **{count}** sounds",
            ephemeral=True
        )

    async def play_queue_callback(self, interaction: discord.Interaction):
        guild = interaction.guild

        if not guild.voice_client:
            if interaction.user.voice:
                await interaction.user.voice.channel.connect()
            else:
                await interaction.response.send_message(
                    "You must be in a voice channel (or move the bot first).",
                    ephemeral=True
                )
                return

        voice_client = guild.voice_client

        if not voice_client.channel:
            await interaction.response.send_message("Bot is not in a voice channel.", ephemeral=True)
            return

        # Acknowledge immediately
        await interaction.response.send_message("Starting queue playback...", ephemeral=True)

        # Start playing in background
        asyncio.create_task(self.play_queue_in_background(guild, voice_client))

    async def play_queue_in_background(self, guild: discord.Guild, voice_client):
        async with queue_locks[guild.id]:
            if not sound_queues[guild.id]:
                return

        while True:
            async with queue_locks[guild.id]:
                if not sound_queues[guild.id]:
                    break
                next_sound = sound_queues[guild.id].pop(0)

            try:
                # Play soundboard sound
                await voice_client.channel.send_sound(next_sound)

                # Wait until it's finished (soundboard sounds are short, but still)
                # Unfortunately discord.py doesn't provide direct "is_playing" for soundboard
                # We can approximate with a delay or listen to voice state (more advanced)
                await asyncio.sleep(3.5)  # ← adjust based on average sound length

            except Exception as e:
                print(f"Error playing soundboard sound: {e}")
                break

        print(f"Queue finished for guild {guild.name}")


@bot.event
async def on_ready():
    logger.info(f"{bot.user} has connected to Discord!")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")


@bot.tree.command(name="soundboard", description="Show the soundboard")
async def soundboard(interaction: discord.Interaction):
    """Show the soundboard with available sounds"""
    if not interaction.guild:
        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )
        return
    
    loaded = await load_sounds(interaction.guild)
    
    if not loaded or not available_sounds:
        await interaction.response.send_message(
            "❌ No soundboard sounds found in this server!\n\n"
            "**To add soundboard sounds:**\n"
            "1. Go to your Discord server settings\n"
            "2. Navigate to **Soundboard** (or Audio)\n"
            "3. Add sounds to your server's soundboard\n"
            "4. Try `/soundboard` again",
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title="🎵 Server Soundboard",
        description=f"Available sounds: {len(available_sounds)}",
        color=discord.Color.blue()
    )
    
    for sound_name in list(available_sounds.keys())[:25]:
        embed.add_field(name=" ", value=f"• {sound_name}", inline=False)
    
    view = SoundboardView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="listsounds", description="List all available sounds")
async def listsounds(interaction: discord.Interaction):
    """List all available soundboard sounds"""
    if not interaction.guild:
        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )
        return
    
    loaded = await load_sounds(interaction.guild)
    
    if not loaded or not available_sounds:
        await interaction.response.send_message(
            "❌ No soundboard sounds found in this server.",
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title="📊 Server Soundboard Sounds",
        description=f"Total: {len(available_sounds)}",
        color=discord.Color.green()
    )
    
    # Add sounds in chunks due to Discord field limit
    chunk_size = 5
    sounds_list = list(available_sounds.keys())
    
    for i in range(0, len(sounds_list), chunk_size):
        chunk = sounds_list[i:i+chunk_size]
        embed.add_field(
            name="Sounds" if i == 0 else " ",
            value="\n".join([f"`{s}`" for s in chunk]),
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# Run the bot
def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError(
            "DISCORD_TOKEN not found in .env file. "
            "Please add your bot token to the .env file."
        )
    
    bot.run(token)


if __name__ == "__main__":
    main()
