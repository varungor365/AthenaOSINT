"""
Telegram Bot Handler for AthenaOSINT.

This module manages the Telegram bot interface, allowing users to
control AthenaOSINT remotely.
"""

import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from loguru import logger
import asyncio
import threading

from config import get_config
from core.engine import AthenaEngine

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🦅 *AthenaOSINT Bot Online*\n\nSend a target (email, username, domain) to start a scan.\nCommands:\n/scan [target] - Run full scan\n/help - Show help",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
*AthenaOSINT Bot Help*

Usage:
1. Simply send a target to scan it instantly.
2. Use `/scan <target>` for explicit scanning.

*Target Types:*
- Email: `target@example.com`
- Username: `targetuser`
- Domain: `example.com`

*Advanced:*
The bot uses the configured modules on the server.
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=help_text,
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages as potential targets."""
    target = update.message.text
    if target.startswith('/'):
        return # Ignore other commands
        
    await run_scan_command(update, context, target)

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /scan command."""
    if not context.args:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠ Please provide a target: `/scan <target>`", parse_mode='Markdown')
        return
    
    target = context.args[0]
    await run_scan_command(update, context, target)

async def run_scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE, target: str):
    """Execute the scan logic."""
    chat_id = update.effective_chat.id
    
    await context.bot.send_message(chat_id=chat_id, text=f"🔍 *Scanning:* `{target}`\nStarted Athena Engine...", parse_mode='Markdown')
    
    # We need to run the blocking scan in a separate thread so we don't block the Async bot loop
    # However, since this is a simple implementation, we'll try to use asyncio.to_thread if available or just run it synchronously (blocking bot) for now 
    # to keep it robust within this script constraint.
    # BETTER: Run in thread.
    
    def _scan_wrapper():
        try:
            engine = AthenaEngine(target, use_intelligence=True, quiet=True)
            modules = ['sherlock', 'theharvester', 'holehe', 'subfinder', 'leak_checker']
            engine.run_scan(modules)
            return engine
        except Exception as e:
            return str(e)

    # loop = asyncio.get_running_loop()
    # result = await loop.run_in_executor(None, _scan_wrapper)
    
    # For simplicity in this environment:
    result = await asyncio.to_thread(_scan_wrapper)
    
    if isinstance(result, str):
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Scan failed: {result}")
    else:
        # Success
        summary = result.profile.get_summary()
        report_path = result.generate_report('json') # Generate a JSON to verify
        
        # Build message
        msg = f"✅ *Scan Complete for {target}*\n\n"
        msg += f"📧 Emails: {summary['emails']}\n"
        msg += f"👤 Usernames: {summary['usernames']}\n"
        msg += f"🌐 Domains: {summary['domains']}\n"
        msg += f"🔓 Breaches: {summary['breaches']}\n"
        msg += f"🤖 Risk Score: {result.profile.raw_data.get('intelligence_analysis', {}).get('risk_score', 'N/A')}\n"
        
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
        
        # Send Report File?
        # await context.bot.send_document(chat_id=chat_id, document=open(report_path, 'rb'))


def run_bot():
    """Start the bot."""
    token = get_config().get('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in config")
        return

    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('scan', scan_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🦅 AthenaOSINT Bot started polling...")
    application.run_polling()
