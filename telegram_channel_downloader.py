#!/usr/bin/env python3
"""
Telegram Channel Downloader
Downloads all media, messages, and files from a given Telegram channel.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from telethon import TelegramClient
    from telethon.tl.types import (
        MessageMediaPhoto,
        MessageMediaDocument,
        MessageMediaWebPage,
        MessageService
    )
    from telethon.errors import SessionPasswordNeededError, FloodWaitError
except ImportError:
    print("Error: Telethon library not found.")
    print("Install it with: pip install telethon")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TelegramChannelDownloader:
    """Download all contents from a Telegram channel."""

    def __init__(self, api_id: int, api_hash: str, phone: str, session_name: str = "downloader"):
        """
        Initialize the Telegram downloader.

        Args:
            api_id: Telegram API ID (get from https://my.telegram.org)
            api_hash: Telegram API Hash
            phone: Phone number with country code (e.g., +1234567890)
            session_name: Name for the session file
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.stats = {
            'messages': 0,
            'photos': 0,
            'videos': 0,
            'documents': 0,
            'audio': 0,
            'errors': 0
        }

    async def connect(self):
        """Connect to Telegram and authenticate."""
        await self.client.connect()

        if not await self.client.is_user_authorized():
            logger.info("First time login - sending code request...")
            await self.client.send_code_request(self.phone)

            try:
                code = input('Enter the code you received: ')
                await self.client.sign_in(self.phone, code)
            except SessionPasswordNeededError:
                password = input('Two-step verification enabled. Enter your password: ')
                await self.client.sign_in(password=password)

        logger.info("Successfully connected to Telegram")

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to remove invalid characters."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:255]  # Limit filename length

    def create_download_directory(self, channel_name: str) -> Path:
        """Create directory structure for downloads."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_channel_name = self._sanitize_filename(channel_name)
        base_dir = Path(f"downloads/{safe_channel_name}_{timestamp}")

        # Create subdirectories
        (base_dir / "photos").mkdir(parents=True, exist_ok=True)
        (base_dir / "videos").mkdir(parents=True, exist_ok=True)
        (base_dir / "documents").mkdir(parents=True, exist_ok=True)
        (base_dir / "audio").mkdir(parents=True, exist_ok=True)
        (base_dir / "messages").mkdir(parents=True, exist_ok=True)

        return base_dir

    async def download_media(self, message, base_dir: Path) -> Optional[str]:
        """Download media from a message."""
        try:
            if message.media:
                if isinstance(message.media, MessageMediaPhoto):
                    file_path = base_dir / "photos" / f"photo_{message.id}.jpg"
                    await self.client.download_media(message, file_path)
                    self.stats['photos'] += 1
                    return str(file_path)

                elif isinstance(message.media, MessageMediaDocument):
                    doc = message.media.document

                    # Determine file type and directory
                    mime_type = doc.mime_type if hasattr(doc, 'mime_type') else ''

                    if 'video' in mime_type:
                        subdir = "videos"
                        self.stats['videos'] += 1
                    elif 'audio' in mime_type or 'ogg' in mime_type:
                        subdir = "audio"
                        self.stats['audio'] += 1
                    else:
                        subdir = "documents"
                        self.stats['documents'] += 1

                    # Get original filename or create one
                    filename = None
                    for attr in doc.attributes:
                        if hasattr(attr, 'file_name'):
                            filename = self._sanitize_filename(attr.file_name)
                            break

                    if not filename:
                        ext = mime_type.split('/')[-1] if '/' in mime_type else 'bin'
                        filename = f"file_{message.id}.{ext}"

                    file_path = base_dir / subdir / filename
                    await self.client.download_media(message, file_path)
                    return str(file_path)

            return None

        except FloodWaitError as e:
            logger.warning(f"Rate limited. Waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            return await self._download_media(message, base_dir)

        except Exception as e:
            logger.error(f"Error downloading media from message {message.id}: {e}")
            self.stats['errors'] += 1
            return None

    async def download_channel(self, channel_username: str, limit: Optional[int] = None):
        """
        Download all contents from a channel.

        Args:
            channel_username: Channel username (with or without @)
            limit: Maximum number of messages to download (None for all)
        """
        try:
            await self.connect()

            # Clean channel username
            if channel_username.startswith('@'):
                channel_username = channel_username[1:]

            logger.info(f"Fetching channel: {channel_username}")

            # Get channel entity
            try:
                channel = await self.client.get_entity(channel_username)
            except Exception as e:
                logger.error(f"Could not find channel '{channel_username}': {e}")
                return

            # Create download directory
            base_dir = self._create_download_directory(channel.title or channel_username)
            logger.info(f"Saving to: {base_dir}")

            # Create messages log file
            messages_file = base_dir / "messages" / "messages.txt"
            messages_json_file = base_dir / "messages" / "messages.json"

            import json
            messages_data = []

            with open(messages_file, 'w', encoding='utf-8') as f:
                f.write(f"Channel: {channel.title or channel_username}\n")
                f.write(f"Download started: {datetime.now()}\n")
                f.write("=" * 80 + "\n\n")

            # Download messages
            logger.info("Starting download...")
            async for message in self.client.iter_messages(channel, limit=limit):
                # Skip service messages
                if isinstance(message, MessageService):
                    continue

                self.stats['messages'] += 1

                # Download media if present
                media_path = None
                if message.media and not isinstance(message.media, MessageMediaWebPage):
                    media_path = await self._download_media(message, base_dir)

                # Save message text
                message_data = {
                    'id': message.id,
                    'date': message.date.isoformat() if message.date else None,
                    'text': message.text or '',
                    'media_path': media_path,
                    'views': message.views,
                    'forwards': message.forwards
                }
                messages_data.append(message_data)

                # Write to text file
                with open(messages_file, 'a', encoding='utf-8') as f:
                    f.write(f"Message ID: {message.id}\n")
                    f.write(f"Date: {message.date}\n")
                    if message.text:
                        f.write(f"Text: {message.text}\n")
                    if media_path:
                        f.write(f"Media: {media_path}\n")
                    f.write("-" * 80 + "\n\n")

                # Progress update
                if self.stats['messages'] % 100 == 0:
                    logger.info(f"Downloaded {self.stats['messages']} messages...")

            # Save JSON
            with open(messages_json_file, 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, indent=2, ensure_ascii=False)

            # Print statistics
            logger.info("\n" + "=" * 50)
            logger.info("Download completed!")
            logger.info(f"Total messages: {self.stats['messages']}")
            logger.info(f"Photos: {self.stats['photos']}")
            logger.info(f"Videos: {self.stats['videos']}")
            logger.info(f"Documents: {self.stats['documents']}")
            logger.info(f"Audio files: {self.stats['audio']}")
            logger.info(f"Errors: {self.stats['errors']}")
            logger.info(f"Saved to: {base_dir.absolute()}")
            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"Error downloading channel: {e}")
            raise

        finally:
            await self.client.disconnect()


async def main():
    """Main entry point."""
    print("=" * 60)
    print("Telegram Channel Downloader")
    print("=" * 60)
    print("\nTo get your API credentials:")
    print("1. Go to https://my.telegram.org")
    print("2. Log in with your phone number")
    print("3. Go to 'API development tools'")
    print("4. Create an app to get api_id and api_hash\n")

    # Get credentials
    try:
        api_id = input("Enter your API ID: ").strip()
        api_hash = input("Enter your API Hash: ").strip()
        phone = input("Enter your phone number (with country code, e.g., +1234567890): ").strip()
        channel = input("Enter channel username (e.g., @channelname or channelname): ").strip()

        limit_input = input("Enter message limit (press Enter for all messages): ").strip()
        limit = int(limit_input) if limit_input else None

        # Validate inputs
        if not all([api_id, api_hash, phone, channel]):
            print("Error: All fields are required!")
            return

        api_id = int(api_id)

    except ValueError as e:
        print(f"Error: Invalid input - {e}")
        return
    except KeyboardInterrupt:
        print("\nCancelled by user")
        return

    # Create downloader and start
    downloader = TelegramChannelDownloader(api_id, api_hash, phone)

    try:
        await downloader.download_channel(channel, limit)
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
