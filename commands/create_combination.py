import discord
import logging
from database import conn, c
from commands import soundboard

logger = logging.getLogger(__name__)


class SoundboardCreateCombinations(discord.ui.View):
    """View with buttons for selecting sounds"""
    
    def __init__(self, sound_name: str, sound_queues, queue_locks):
        super().__init__(timeout=None)
        self.sound_name = sound_name
        self.sound_queues = sound_queues
        self.queue_locks = queue_locks
        self.add_sound_buttons()
        self.add_item(self.save_combination_button())

    def add_sound_buttons(self):
        for sound_name in list(soundboard.available_sounds.keys()):  # leave space for Play button
            button = discord.ui.Button(
                label=sound_name,
                style=discord.ButtonStyle.primary,
                emoji=soundboard.available_sounds[sound_name].emoji if soundboard.available_sounds[sound_name].emoji else None,
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
        if sound_name not in soundboard.available_sounds:
            await interaction.response.send_message("Sound not found.", ephemeral=True)
            return

        guild = interaction.guild
        async with self.queue_locks[guild.id]:
            self.sound_queues[guild.id].append(soundboard.available_sounds[sound_name])

        count = len(self.sound_queues[guild.id])
        await interaction.response.send_message(
            f"**{sound_name}** added to queue → position **{count}**\n"
            f"Queue size: **{count}** sounds",
            ephemeral=True
        )

    async def save_combination(self, sound_name: str, interaction: discord.Interaction):
        guild = interaction.guild
        async with self.queue_locks[guild.id]:
            try:
                query = "INSERT INTO sound_combination (server_id, sound_name) VALUES (%s, %s) RETURNING id"
                c.execute(query, (guild.id, sound_name))
                id = c.fetchone()[0]
                for sound in self.sound_queues[guild.id]:
                    c.execute(
                        "INSERT INTO sound_combination_sounds (combination_id, sound_id) VALUES (%s, %s)",
                        (id, sound.id)
                    )
                conn.commit()
            except Exception as e:
                logger.error(f"Error saving combination to database: {e}")
                await interaction.response.send_message("Failed to save combination.", ephemeral=True)
                return
        await interaction.response.send_message(f"Combinations for **{sound_name}** saved!", ephemeral=True)


def setup_create_combination_command(bot, sound_queues, queue_locks):
    """Register the create_combination command"""
    
    @bot.tree.command(name="create_combination", description="Play a sound in your voice channel")
    @discord.app_commands.describe(sound="Name to create soundbar combination")
    async def create_combination(interaction: discord.Interaction, sound: str):
        from commands.soundboard import load_sounds
        
        sound_queues[interaction.guild.id] = []
        c.execute("SELECT sound_name FROM sound_combination WHERE server_id = %s AND sound_name = %s", (interaction.guild.id, sound))
        result = c.fetchone()
        if result:
            await interaction.response.send_message(
                f"❌ A combination with the name **{sound}** already exists. Please choose a different name.",
                ephemeral=True
            )
            return
        
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )
            return
        
        loaded = await load_sounds(interaction.guild)
        
        if not loaded or not soundboard.available_sounds:
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
            description=f"Available sounds: {len(soundboard.available_sounds)}",
            color=discord.Color.blue()
        )
        
        for sound_name in list(soundboard.available_sounds.keys()):
            embed.add_field(name=" ", value=f"• {sound_name}", inline=False)
        
        view = SoundboardCreateCombinations(sound, sound_queues, queue_locks)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
