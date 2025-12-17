#!/usr/bin/env python3
"""
Telegram bot launcher for AthenaOSINT.

This script starts the Telegram bot for remote OSINT scanning.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from bot.bot_handler import AthenaBot
from config import get_config
from loguru import logger


def main():
    """Start the Telegram bot."""
    config = get_config()
    
    token = config.get('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not configured in .env file")
        print("\nPlease:")
        print("1. Create a bot using @BotFather on Telegram")
        print("2. Add the token to your .env file: TELEGRAM_BOT_TOKEN=your_token_here")
        sys.exit(1)
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║                   AthenaOSINT Telegram Bot                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Bot is starting...
Press CTRL+C to stop the bot
    """)
    
    try:
        bot = AthenaBot(token)
        bot.run()
    except KeyboardInterrupt:
        print("\n\nShutting down bot...")
        logger.info("Telegram bot stopped")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
