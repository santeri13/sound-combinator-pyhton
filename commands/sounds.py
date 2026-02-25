import discord
from discord.ext import commands
from commands import soundboard


class SoundsCog(commands.Cog):
    """Sounds command cog"""
    
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="listsounds", description="List all available sounds")
    async def listsounds(self, interaction: discord.Interaction):
        """List all available soundboard sounds"""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )
            return
        
        loaded = await soundboard.load_sounds(interaction.guild)
        print(f"Loaded sounds for guild {interaction.guild.name}: {loaded} sounds available: {list(soundboard.available_sounds.keys())}")
        
        if not loaded or not soundboard.available_sounds:
            await interaction.response.send_message(
                "❌ No soundboard sounds found in this server.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📊 Server Soundboard Sounds",
            description=f"Total: {len(soundboard.available_sounds)}",
            color=discord.Color.green()
        )
        # Add sounds in chunks due to Discord field limit
        chunk_size = 5
        sounds_list = list(soundboard.available_sounds.keys())
        
        for i in range(0, len(sounds_list), chunk_size):
            chunk = sounds_list[i:i+chunk_size]
            embed.add_field(
                name="Sounds" if i == 0 else " ",
                value="\n".join([f"`{s}`" for s in chunk]),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    """Setup function called by discord.py when loading the cog"""
    await bot.add_cog(SoundsCog(bot))


