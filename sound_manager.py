"""
Utility script for managing Discord soundboard bot configuration
"""

import os
from dotenv import load_dotenv


def check_env_setup():
    """Check if .env file is properly configured"""
    load_dotenv()
    
    token = os.getenv("DISCORD_TOKEN")
    
    print("\n" + "=" * 50)
    print("🔍 Discord Bot Configuration Check")
    print("=" * 50 + "\n")
    
    if token and token != "your_bot_token_here":
        print("✅ DISCORD_TOKEN is set")
    else:
        print("❌ DISCORD_TOKEN is not set or using placeholder")
        print("   Go to: https://discord.com/developers/applications")
        print("   Create a bot and copy the token to .env")
    
    print("\n" + "=" * 50)
    print("📝 Soundboard Setup:")
    print("=" * 50)
    print("The bot uses Discord's native soundboard sounds.")
    print("\nTo add sounds:")
    print("  1. Go to your Discord server settings")
    print("  2. Navigate to Soundboard (or Audio)")
    print("  3. Add sounds to your server's soundboard")
    print("  4. Use /soundboard command in Discord to play them")
    print()


def get_setup_instructions():
    """Print detailed setup instructions"""
    instructions = """
📚 SETUP GUIDE FOR DISCORD SOUNDBOARD BOT
==========================================

STEP 1: Create Discord Bot
   • Go to https://discord.com/developers/applications
   • Click "New Application"
   • Name your bot (e.g., "SoundBot")
   • Go to "Bot" section → "Add Bot"
   • Copy the TOKEN (keep it secret!)

STEP 2: Configure Bot Permissions
   • OAuth2 → URL Generator
   • Scopes: ✓ bot
   • Permissions:
     ✓ Send Messages
     ✓ Use Slash Commands
     ✓ Read Message History
     ✓ Connect (Voice)
     ✓ Speak (Voice)
   • Copy the URL and open to invite bot to server

STEP 3: Configure .env
   • Open .env file
   • Add your bot token:
     DISCORD_TOKEN=your_token_here

STEP 4: Add Soundboard Sounds
   • Go to your Discord server settings
   • Navigate to Soundboard (or Audio section)
   • Add .mp3 or other supported sound files
   • These will be available to the bot automatically

STEP 5: Run Bot
   • python main.py

STEP 6: Use Soundboard
   • In Discord, type: /soundboard
   • Click sound buttons to play
   • Or use /playsound <sound_name>

🎯 COMMANDS:
   /soundboard - Show interactive soundboard
   /playsound <sound> - Play a specific sound
   /listsounds - List all available sounds
   /stop - Stop current sound
   /disconnect - Disconnect bot

📞 NEED HELP?
   Discord.py: https://discordpy.readthedocs.io/
   Discord API: https://discord.com/developers/docs
    """
    print(instructions)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        get_setup_instructions()
    else:
        check_env_setup()


