# Telegram Channel Downloader

A robust Python program to download all contents (messages, photos, videos, documents, audio) from any Telegram channel.

## Features

- **Complete Download**: Downloads all messages, media files, and documents from a channel
- **Organized Storage**: Automatically organizes downloads into categorized folders (photos, videos, documents, audio, messages)
- **Resume Support**: Uses session files to avoid re-authentication
- **Rate Limit Handling**: Automatically handles Telegram's rate limits with exponential backoff
- **Progress Tracking**: Shows real-time progress and statistics
- **Export Formats**: Saves messages in both text and JSON formats
- **Error Recovery**: Continues downloading even if individual files fail

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Get Telegram API credentials:
   - Go to https://my.telegram.org
   - Log in with your phone number
   - Navigate to "API development tools"
   - Create an application to get your `api_id` and `api_hash`

## Usage

### Interactive Mode

Simply run the script and follow the prompts:

```bash
python telegram_channel_downloader.py
```

You'll be asked to provide:
- API ID
- API Hash
- Phone number (with country code, e.g., +1234567890)
- Channel username (e.g., @channelname or channelname)
- Message limit (optional - press Enter to download all messages)

### Programmatic Usage

You can also use it as a module:

```python
import asyncio
from telegram_channel_downloader import TelegramChannelDownloader

async def download():
    downloader = TelegramChannelDownloader(
        api_id=YOUR_API_ID,
        api_hash="YOUR_API_HASH",
        phone="+1234567890"
    )
    await downloader.download_channel("channelname", limit=None)

asyncio.run(download())
```

## Output Structure

Downloaded content is organized as follows:

```
downloads/
└── ChannelName_20251027_204500/
    ├── photos/          # Image files
    ├── videos/          # Video files
    ├── documents/       # Documents and other files
    ├── audio/           # Audio files and voice messages
    └── messages/
        ├── messages.txt # Human-readable message log
        └── messages.json # Structured JSON data
```

## Features Explained

### Authentication
- First-time users will receive a verification code on Telegram
- Session is saved locally (`.session` file) for future runs
- Supports two-factor authentication

### Media Detection
- Automatically categorizes files by MIME type
- Preserves original filenames when available
- Generates meaningful names for unnamed files

### Error Handling
- Gracefully handles network interruptions
- Continues downloading after rate limits
- Logs all errors for review

### Statistics
After completion, you'll see:
- Total messages downloaded
- Number of photos, videos, documents, and audio files
- Any errors encountered
- Location of downloaded files

## Troubleshoties

### "Could not find channel"
- Ensure the channel is public or you're a member
- Check the username is correct (without https://t.me/)

### Rate Limiting
- The script automatically handles rate limits
- Large channels may take considerable time

### Authentication Issues
- Delete the `.session` file and try again
- Verify your API credentials are correct

## Notes

- **Privacy**: Your API credentials and session files contain sensitive information. Keep them secure.
- **Legal**: Only download content from channels you have permission to access.
- **Performance**: Large channels with extensive media may require significant disk space and time.

## Requirements

- Python 3.7+
- Telethon library
- Active Telegram account
- Valid API credentials from my.telegram.org

## License

This script is provided as-is for educational purposes.
