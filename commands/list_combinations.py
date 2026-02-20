import discord
from database import c


def setup_list_combinations_command(bot):
    """Register the list_combinations command"""
    
    @bot.tree.command(name="list_combinations", description="List all created combinations")
    async def list_combinations(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )
            return
        
        query = "SELECT server_id, sound_name FROM sound_combination WHERE server_id = %s"
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
