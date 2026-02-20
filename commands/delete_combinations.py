import discord
import logging
from database import conn, c
from commands.utils import fetched_combinations

logger = logging.getLogger(__name__)


class DeleteCombinationView(discord.ui.View):
    """View for deleting combinations"""
    
    def __init__(self, sound_combinations):
        super().__init__(timeout=None)
        self.sound_combinations = sound_combinations
        self.add_combination_buttons()
        print("DeleteCombinationView initialized with combinations: ", sound_combinations)

    def add_combination_buttons(self):
        for sound_name in list(self.sound_combinations.keys())[:20]:  # limit to 20 for display
            button = discord.ui.Button(
                label=sound_name[:80],
                style=discord.ButtonStyle.danger
            )
            button.callback = self.delete_combination_callback(sound_name)
            self.add_item(button)

    def delete_combination_callback(self, sound_name: str):
        async def callback(interaction: discord.Interaction):
            await self.delete_combination(interaction, sound_name)
        return callback

    async def delete_combination(self, interaction: discord.Interaction, sound_name: str):
        guild = interaction.guild
        try:
            c.execute(
                "DELETE FROM sound_combination_sounds WHERE combination_id = (SELECT id FROM sound_combination WHERE server_id = %s AND sound_name = %s)",
                (guild.id, sound_name)
            )
            c.execute(
                "DELETE FROM sound_combination WHERE server_id = %s AND sound_name = %s",
                (guild.id, sound_name)
            )
            conn.commit()
            await interaction.response.send_message(f"Combination **{sound_name}** deleted!", ephemeral=True)
        except Exception as e:
            logger.error(f"Error deleting combination from database: {e}")
            await interaction.response.send_message("Failed to delete combination.", ephemeral=True)


def setup_delete_combinations_command(bot):
    """Register the delete_combinations command"""
    
    @bot.tree.command(name="delete_combinations", description="Delete a combination for this server")
    async def delete_combinations(interaction: discord.Interaction):
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
        
        if not results:
            await interaction.response.send_message(
                "❌ No soundboard combinations found in this server.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🗑️ Delete Soundboard Combinations",
            description=f"Total: {len(results)}",
            color=discord.Color.red()
        )
        
        for row in results:
            embed.add_field(name=" ", value=f"• {row[0]}", inline=False)
        
        view = DeleteCombinationView(sound_combinations)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
