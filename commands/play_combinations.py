import discord
import asyncio
from database import c
from commands.utils import fetched_combinations


class SoundboardCombinationView(discord.ui.View):
    """View for displaying saved combinations"""
    
    def __init__(self, sound_combinations):
        super().__init__(timeout=None)
        self.sound_combinations = sound_combinations
        self.add_sound_buttons()

    def add_sound_buttons(self):
        for sound_name in list(self.sound_combinations.keys()):  # leave space for Play button
            button = discord.ui.Button(
                label=sound_name[:80],
                style=discord.ButtonStyle.primary
            )
            button.callback = self.play_sound_callback(sound_name)
            self.add_item(button)
    
    def play_sound_callback(self, sound_name: str):
        async def callback(interaction: discord.Interaction):
            await self.play_sound(interaction, self.sound_combinations[sound_name])
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
        await interaction.response.send_message(f"Playing combination ...", ephemeral=True)

        for sound_id in sound_ids:
            try:
                sound = guild.get_soundboard_sound(sound_id)
                await voice_client.channel.send_sound(sound)

                # Wait until it's finished (soundboard sounds are short, but still)
                await asyncio.sleep(3.5)  # ← adjust based on average sound length

            except Exception as e:
                print(f"Error playing soundboard sound: {e}")
                break
        
        # Disconnect from voice channel after all sounds are played
        await voice_client.disconnect()


def setup_play_created_combinations_command(bot):
    """Register the play_created_combinations command"""
    
    @bot.tree.command(name="play_created_combinations", description="Play createdcombinations for this server")
    async def play_created_combinations(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )
            return
        
        query = "SELECT sound_name FROM sound_combination WHERE server_id = %s"
        c.execute(query, (interaction.guild.id,))
        results = c.fetchall()

        sound_combinations = fetched_combinations({}, results, c, interaction.guild.id)

        if not sound_combinations:
            await interaction.response.send_message(
                "❌ No soundboard combinations found in this server.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🎵 Combinations soundboard",
            description=f"Available sounds: {len(sound_combinations)}",
            color=discord.Color.blue()
        )
        
        for sound_name in list(sound_combinations.keys()):
            embed.add_field(name=" ", value=f"• {sound_name}", inline=False)

        view = SoundboardCombinationView(sound_combinations)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
