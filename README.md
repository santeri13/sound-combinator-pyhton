# Discord Soundboard Bot

A Discord bot that plays your server's native soundboard sounds directly in voice channels.

## Features

- 🎵 **Soundboard Integration**: Uses Discord's native soundboard sounds
- 🔊 **Voice Integration**: Plays sounds in the voice channel where the user is located
- 📊 **Easy Setup**: No configuration needed beyond the bot token
- ⏹️ **Playback Control**: Stop sounds or disconnect from voice channels
- 🎯 **Slash Commands**: Modern Discord slash command interface

## Prerequisites

- Python 3.8 or higher
- Discord Bot Account

## Setup

1. **Download and extract the bot files** to your desired location.

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a Discord Bot:**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Name your bot
   - Go to "Bot" section and click "Add Bot"
   - Copy the bot token

4. **Configure permissions:**
   - In the Developer Portal, go to OAuth2 > URL Generator
   - Select scopes: `bot`
   - Select permissions:
     - `Send Messages`
     - `Use Slash Commands`
     - `Read Message History`
     - `Connect` (Voice)
     - `Speak` (Voice)
   - Copy the generated URL and open it to invite the bot to your server

5. **Add your bot token:**
   - Open `.env` file
   - Replace Discord bot token with your bot token and your Discord user id with your user id:
     ```
     DISCORD_TOKEN=YOUR_ACTUAL_TOKEN_HERE
     OWNER_ID=YOUR_DISCORD_ID
     ```

6. **Add soundboard sounds to your server:**
   - Go to your Discord server settings
   - Navigate to **Soundboard** (or **Audio**)
   - Add sounds to your server's soundboard
   - These will automatically be available to the bot

7. **Run the bot:**
   ```bash
   python main.py
   ```

## Commands

- `/create_combination` - Create a sound combination and save it
- `/list_combinations` - List your saved combinations
- `/delete_combinations` - Delete a saved combination
- `/play_created_combinations` - Play created combinations on your server channel
- `/soundboard` - Show interactive soundboard and combine sound
- `/sync` - Only for bot owner, sync commands globaly

## Usage

1. **To use the soundboard:**
   - Join a voice channel
   - Type `/soundboard` in any text channel
   - Click the button for the sound you want to play
   - The bot will join your voice channel and play the sound

2. **Managing server soundboard:**
   - Server soundboard sounds are managed in your server settings
   - The bot will automatically detect and play them

## File Structure

```
sound combinator python/
├── main.py              # Main bot script
├── requirements.txt     # Python dependencies
├── .env                 # Configuration file (add your token here)
├── README.md            # This file
├── sound_manager.py     # Utility for checking configuration
├── legal                # Privacy policy and term of service
├── keep_alive.py        # Create Flask server which recive ping that Render do not shutdown it 
└── commands             # Contain commands for bot
```

## Troubleshooting

**Bot doesn't respond:**
- Ensure the bot token is correct in `.env`
- Make sure the bot is invited to your server
- Check that slash commands are enabled for the bot

**No sounds showing up:**
- Make sure you've added sounds to your server's soundboard in server settings
- Run `/listsounds` to verify the bot can see them
- Check the bot has permission to read messages

**Sound plays but no audio:**
- Check your server's soundboard sounds are valid
- Ensure your Discord voice settings are configured correctly
- Try a different sound to test

## Support

For issues or questions, check:
- [discord.py documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Documentation](https://discord.com/developers/docs)

