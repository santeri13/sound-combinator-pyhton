import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import logging
import sqlite3
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
saved_sound_combinations = {}

#Database connection (for future persistence, not used in current code)
conn = sqlite3.connect('soundbar_combinations_db.db')
c = conn.cursor()


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
            print(sound)
            available_sounds[sound.name] = sound
            logger.info(f"Loaded soundboard sound: {sound.name}")
        
        logger.info(f"Loaded {len(available_sounds)} soundboard sounds")
        return True
    
    except Exception as e:
        logger.error(f"Error loading soundboard sounds: {e}")
        return False
    
class SoundboardCreateCombinations(discord.ui.View):
    """View with buttons for selecting sounds"""
    
    def __init__(self, sound_name: str):
        super().__init__(timeout=None)
        self.sound_name = sound_name
        self.add_sound_buttons()
        self.add_item(self.save_combination_button())

    def add_sound_buttons(self):
        for sound_name in list(available_sounds.keys())[:20]:  # leave space for Play button
            button = discord.ui.Button(
                label=sound_name[:80],
                style=discord.ButtonStyle.primary,
                emoji=available_sounds[sound_name].emoji if available_sounds[sound_name].emoji else None,
            )
            button.callback = self.add_combination_callback(sound_name)
            self.add_item(button)

    def save_combination_button(self):
        button = discord.ui.Button(
            label="▶️ Save Combinations",
            style=discord.ButtonStyle.green,
            row=4  # bottom row
        )
        async def wrapped_save_callback(interaction: discord.Interaction):
            await self.save_combination(self.sound_name, interaction)
        
        button.callback = wrapped_save_callback
        return button

    def add_combination_callback(self, sound_name: str):
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

    async def save_combination(self, sound_name: str, interaction: discord.Interaction):
        guild = interaction.guild
        async with queue_locks[guild.id]:
            try:
                query = "INSERT INTO sound_combination (server_id, sound_name) VALUES (?, ?) returning id"
                id = c.execute(query, (guild.id, sound_name)).fetchone()[0]
                for sound in sound_queues[guild.id]:
                    c.execute(
                        "INSERT INTO sound_combination_sounds (combination_id, sound_id) VALUES (?, ?)",
                        (id, sound.id)
                    )
                conn.commit()
            except Exception as e:
                logger.error(f"Error saving combination to database: {e}")
                await interaction.response.send_message("Failed to save combination.", ephemeral=True)
                return
        await interaction.response.send_message(f"Combinations for **{sound_name}** saved!", ephemeral=True)

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
                style=discord.ButtonStyle.primary,
                emoji=available_sounds[sound_name].emoji if available_sounds[sound_name].emoji else None,
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

class SoundboardCombinationView(discord.ui.View):
    """View for displaying saved combinations"""
    
    def __init__(self, combination_name: str):
        super().__init__(timeout=None)
        self.add_sound_buttons()
        self.combination_name = combination_name
        # In a real implementation, you would load the sounds for this combination and create buttons to play them

    def add_sound_buttons(self):
        for sound_name in list(available_sounds.keys())[:20]:  # leave space for Play button
            button = discord.ui.Button(
                label=sound_name[:80],
                style=discord.ButtonStyle.primary,
                emoji=available_sounds[sound_name].emoji if available_sounds[sound_name].emoji else None,
            )
            button.callback = self.play_sound_callback(sound_name)
            self.add_item(button)
    
    def play_sound_callback(self, sound_name: str):
        async def callback(interaction: discord.Interaction):
            query = "SELECT sound_id FROM sound_combination_sounds WHERE combination_id = (SELECT id FROM sound_combination WHERE server_id = ? AND sound_name = ?)"
            c.execute(query, (interaction.guild.id, self.combination_name))
            results = c.fetchall()
            await self.play_sound(interaction,results)
        return callback

    async def play_sound(self, interaction: discord.Interaction, sound_ids: list):
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
        await interaction.response.send_message(f"Playing combination **{self.combination_name}**...", ephemeral=True)

        for sound_id in sound_ids:
            try:
                # Play soundboard sound by ID
                await voice_client.channel.send_sound(available_sounds[sound_id[0]])

                # Wait until it's finished (soundboard sounds are short, but still)
                await asyncio.sleep(3.5)  # ← adjust based on average sound length

            except Exception as e:
                print(f"Error playing soundboard sound: {e}")
                break

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
    sound_queues[interaction.guild.id] = []
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

@bot.tree.command(name="create_combination", description="Play a sound in your voice channel")
@discord.app_commands.describe(sound="Name to create soundbar combination")
async def playsound(interaction: discord.Interaction, sound: str):
    sound_queues[interaction.guild.id] = []
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
    
    view = SoundboardCreateCombinations(sound)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="list_combinations", description="List all created combinations")
async def listsounds(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )
        return
    
    
    # For demonstration, we will just list the combinations stored in memory
    query = "SELECT server_id, sound_name FROM sound_combination WHERE server_id = ?"
    c.execute(query, (interaction.guild.id,))
    results = c.fetchall()
    
    guild_combinations = {}
    for row in results:
        server_id, sound_name = row
        if server_id not in guild_combinations:
            guild_combinations[server_id] = []
        guild_combinations[server_id].append(sound_name)
    
    if not guild_combinations:
        await interaction.response.send_message(
            "❌ No soundboard combinations found in this server yet.",
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title="📋 Server Soundboard Combinations",
        description=f"Total: {len(guild_combinations)}",
        color=discord.Color.green()
    )
    
    for server_id, combinations in guild_combinations.items():
        embed.add_field(
            name=f"Combinations for Server ID {server_id}",
            value="\n".join([f"• {c}" for c in combinations]),
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="play_combinations", description="Play combinations for this server")
async def play_combinations(interaction: discord.Interaction):
    
    """Show the soundboard with available sounds"""
    if not interaction.guild:
        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )
        return
    
    query = "SELECT sound_name FROM sound_combination WHERE server_id = ?"
    c.execute(query, (interaction.guild.id,))
    results = c.fetchall()

    if not results:
        await interaction.response.send_message(
            "❌ No soundboard combinations found in this server.",
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title="🎵 Combinations soundboard",
        description=f"Available sounds: {len(results)}",
        color=discord.Color.blue()
    )
    
    for row in results:
        sound_name = row[0]
        embed.add_field(name=" ", value=f"• {sound_name}", inline=False)

    view = SoundboardView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    


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
