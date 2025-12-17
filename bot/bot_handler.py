"""
Telegram bot handler for AthenaOSINT.

This module provides remote OSINT scanning via Telegram bot commands.
"""

import threading
import time
from typing import Dict, Any
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from loguru import logger

from config import get_config
from core.engine import AthenaEngine
from core.validators import validate_target, detect_target_type
from modules import get_available_modules
from intelligence.automator import Automator


class AthenaBot:
    """Telegram bot for AthenaOSINT."""
    
    # Admin user info
    ADMIN_USER_ID = 796354588
    ADMIN_USERNAME = "hackingmasterr"
    
    # Module descriptions with emojis and details
    MODULE_INFO = {
        'sherlock': {
            'emoji': '👤',
            'name': 'Sherlock',
            'desc': 'Find usernames across 400+ social networks',
            'target': 'Username',
            'category': 'Social Media'
        },
        'holehe': {
            'emoji': '📧',
            'name': 'Holehe',
            'desc': 'Check email registration on 120+ websites',
            'target': 'Email',
            'category': 'Email Intelligence'
        },
        'leak_checker': {
            'emoji': '🔓',
            'name': 'Leak Checker',
            'desc': 'Search data breaches and password leaks',
            'target': 'Email/Username',
            'category': 'Security'
        },
        'theharvester': {
            'emoji': '🌐',
            'name': 'TheHarvester',
            'desc': 'Gather emails, subdomains, IPs from search engines',
            'target': 'Domain',
            'category': 'Reconnaissance'
        },
        'subfinder': {
            'emoji': '🔍',
            'name': 'Subfinder',
            'desc': 'Discover subdomains using passive sources',
            'target': 'Domain',
            'category': 'DNS Recon'
        },
        'wayback': {
            'emoji': '⏰',
            'name': 'Wayback Machine',
            'desc': 'Access archived website versions and history',
            'target': 'Domain/URL',
            'category': 'Archives'
        },
        'nuclei': {
            'emoji': '🛡️',
            'name': 'Nuclei',
            'desc': 'Scan for vulnerabilities and misconfigurations',
            'target': 'Domain/IP',
            'category': 'Security Scanning'
        },
        'dnsdumpster': {
            'emoji': '🌍',
            'name': 'DNSDumpster',
            'desc': 'DNS reconnaissance and mapping',
            'target': 'Domain',
            'category': 'DNS Analysis'
        },
        'exiftool': {
            'emoji': '📷',
            'name': 'ExifTool',
            'desc': 'Extract metadata from images and files',
            'target': 'File/Image',
            'category': 'Forensics'
        },
        'auto_dorker': {
            'emoji': '🔎',
            'name': 'Auto Dorker',
            'desc': 'Automated Google Dorks for sensitive files',
            'target': 'Domain',
            'category': 'Google Hacking'
        },
        'cloud_hunter': {
            'emoji': '☁️',
            'name': 'Cloud Hunter',
            'desc': 'Find exposed cloud storage buckets',
            'target': 'Domain/Company',
            'category': 'Cloud Security'
        },
        'crypto_hunter': {
            'emoji': '₿',
            'name': 'Crypto Hunter',
            'desc': 'Track cryptocurrency addresses and transactions',
            'target': 'Crypto Address',
            'category': 'Blockchain'
        },
        'profile_scraper': {
            'emoji': '📱',
            'name': 'Profile Scraper',
            'desc': 'Extract detailed social media profile data',
            'target': 'Username/Profile',
            'category': 'Social Media'
        },
        'sentiment': {
            'emoji': '💭',
            'name': 'Sentiment Analysis',
            'desc': 'Analyze sentiment and reputation online',
            'target': 'Username/Brand',
            'category': 'Analysis'
        },
        'ocr': {
            'emoji': '📸',
            'name': 'OCR Scanner',
            'desc': 'Extract text from images using Tesseract',
            'target': 'Image',
            'category': 'Forensics'
        },
        'email_permutator': {
            'emoji': '✉️',
            'name': 'Email Permutator',
            'desc': 'Generate and verify email address variations',
            'target': 'Name + Domain',
            'category': 'Email Intelligence'
        },
        'job_hunter': {
            'emoji': '💼',
            'name': 'Job Hunter',
            'desc': 'Analyze job postings for tech stack intelligence',
            'target': 'Company',
            'category': 'Business Intelligence'
        },
        'canary_checker': {
            'emoji': '🐦',
            'name': 'Canary Checker',
            'desc': 'Detect honeypots and monitoring systems',
            'target': 'Domain/IP',
            'category': 'OPSEC'
        }
    }
    
    def __init__(self, token: str):
        """Initialize the bot.
        
        Args:
            token: Telegram bot token
        """
        self.token = token
        self.config = get_config()
        self.active_scans: Dict[int, Any] = {}  # user_id -> scan_info
        self.app = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        welcome_message = f"""
🦅 **AthenaOSINT Intelligence Bot** 🦅

Welcome {user.first_name}! (@{user.username or 'user'})
Bot: @ANTHENAa_bot

Advanced Open Source Intelligence Framework for comprehensive target reconnaissance.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 **SCAN COMMANDS**

🎯 `/scan <target>`
Standard OSINT scan with core modules
Example: `/scan john.doe@gmail.com`

⚡ `/quickscan <target>`
Fast scan (2-3 min) - Essential modules only
Example: `/quickscan johndoe`

🔥 `/fullscan <target>`
Comprehensive scan (5-10 min) - All modules
Example: `/fullscan example.com`

🕵️ `/deepscan <target> [depth]`
Recursive intelligence scan with auto-discovery
Example: `/deepscan johndoe 2`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛠️ **UTILITY COMMANDS**

📦 `/modules` - View all OSINT modules with descriptions
📊 `/status` - Check your current scan progress
❓ `/help` - Show this help menu

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ **IMPORTANT NOTES**

• Scans can take 2-15 minutes depending on scope
• One scan per user at a time
• You'll receive real-time updates
• Results include detailed reports

🔐 Use responsibly and ethically!
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"User {user.id} ({user.username}) started the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await self.start_command(update, context)
    
    async def modules_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /modules command."""
        try:
            modules = get_available_modules()
            
            message = "📦 **OSINT MODULES CATALOG**\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            # Group by category
            categories = {}
            for name, info in modules.items():
                mod_info = self.MODULE_INFO.get(name, {})
                category = mod_info.get('category', 'Other')
                if category not in categories:
                    categories[category] = []
                categories[category].append((name, info, mod_info))
            
            for category, mods in sorted(categories.items()):
                message += f"\n**{category.upper()}**\n"
                for name, info, mod_info in mods:
                    status = "🟢" if info['available'] else "🔴"
                    emoji = mod_info.get('emoji', '🔧')
                    desc = mod_info.get('desc', info.get('description', 'OSINT module'))
                    target = mod_info.get('target', info.get('target_type', 'Any'))
                    
                    message += f"\n{status} {emoji} **{name}**\n"
                    message += f"   📝 {desc}\n"
                    message += f"   🎯 Target: {target}\n"
            
            message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += f"**Total Modules:** {len(modules)}\n"
            available = sum(1 for m in modules.values() if m['available'])
            message += f"**Available:** {available}/{len(modules)}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            logger.info(f"User {update.effective_user.id} requested modules list")
        
        except Exception as e:
            logger.error(f"Failed to get modules: {e}")
            await update.message.reply_text("❌ Failed to load modules list.")
    
    async def scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /scan command."""
        user_id = update.effective_user.id
        
        # Check if user has active scan
        if user_id in self.active_scans:
            await update.message.reply_text(
                "⚠️ You already have an active scan. Please wait for it to complete."
            )
            return
        
        # Parse target
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a target.\n\nUsage: `/scan <target>`",
                parse_mode='Markdown'
            )
            return
        
        target = ' '.join(context.args)
        
        # Validate target
        if not validate_target(target):
            await update.message.reply_text(
                f"❌ Invalid target: `{target}`\n\n"
                "Please provide a valid email, username, domain, or phone number.",
                parse_mode='Markdown'
            )
            return
        
        # Start scan
        modules = ['sherlock', 'holehe', 'leak_checker']
        await self._start_scan(update, target, modules, use_intelligence=False)
    
    async def quickscan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quickscan command."""
        user_id = update.effective_user.id
        
        if user_id in self.active_scans:
            await update.message.reply_text(
                "⚠️ You already have an active scan. Please wait for it to complete."
            )
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a target.\n\nUsage: `/quickscan <target>`",
                parse_mode='Markdown'
            )
            return
        
        target = ' '.join(context.args)
        
        if not validate_target(target):
            await update.message.reply_text(
                f"❌ Invalid target: `{target}`",
                parse_mode='Markdown'
            )
            return
        
        # Quick scan with limited modules
        modules = ['sherlock', 'holehe']
        await self._start_scan(update, target, modules, use_intelligence=False)
    
    async def fullscan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /fullscan command."""
        user_id = update.effective_user.id
        
        if user_id in self.active_scans:
            await update.message.reply_text(
                "⚠️ You already have an active scan. Please wait for it to complete."
            )
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a target.\n\nUsage: `/fullscan <target>`",
                parse_mode='Markdown'
            )
            return
        
        target = ' '.join(context.args)
        
        if not validate_target(target):
            await update.message.reply_text(
                f"❌ Invalid target: `{target}`",
                parse_mode='Markdown'
            )
            return
        
        # Full scan with all available modules
        modules = ['sherlock', 'holehe', 'leak_checker', 'theharvester', 'subfinder']
        await self._start_scan(update, target, modules, use_intelligence=True)
    
    async def deepscan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /deepscan command."""
        user_id = update.effective_user.id
        
        if user_id in self.active_scans:
            await update.message.reply_text(
                "⚠️ You already have an active scan. Please wait for it to complete."
            )
            return
        
        if len(context.args) < 1:
            await update.message.reply_text(
                "❌ Please provide a target and optional depth.\n\n"
                "Usage: `/deepscan <target> [depth]`\n"
                "Example: `/deepscan johndoe 2`",
                parse_mode='Markdown'
            )
            return
        
        target = context.args[0]
        depth = int(context.args[1]) if len(context.args) > 1 else 2
        
        # Limit depth
        max_depth = self.config.get('MAX_SCAN_DEPTH', 3)
        if depth > max_depth:
            depth = max_depth
            await update.message.reply_text(
                f"⚠️ Depth limited to {max_depth} (configured maximum)"
            )
        
        if not validate_target(target):
            await update.message.reply_text(
                f"❌ Invalid target: `{target}`",
                parse_mode='Markdown'
            )
            return
        
        # Start deep scan
        await update.message.reply_text(
            f"🔍 Starting deep scan on `{target}` with depth {depth}...\n\n"
            "This may take several minutes. You'll be notified when complete.",
            parse_mode='Markdown'
        )
        
        # Mark as active
        self.active_scans[user_id] = {'target': target, 'type': 'deep'}
        
        # Run in background thread
        thread = threading.Thread(
            target=self._run_deep_scan_background,
            args=(update, target, depth)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"User {user_id} started deep scan on {target} with depth {depth}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        user_id = update.effective_user.id
        
        if user_id in self.active_scans:
            scan_info = self.active_scans[user_id]
            await update.message.reply_text(
                f"🔄 Active scan in progress:\n"
                f"Target: `{scan_info['target']}`\n"
                f"Type: {scan_info['type']}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("No active scans.")
    
    async def _start_scan(
        self,
        update: Update,
        target: str,
        modules: list,
        use_intelligence: bool
    ):
        """Start a background scan.
        
        Args:
            update: Telegram update
            target: Target to scan
            modules: List of modules to use
            use_intelligence: Enable intelligence analysis
        """
        user_id = update.effective_user.id
        target_type = detect_target_type(target)
        
        await update.message.reply_text(
            f"🔍 Scan started for `{target}`\n"
            f"Type: {target_type}\n"
            f"Modules: {', '.join(modules)}\n\n"
            "I'll notify you when it's complete!",
            parse_mode='Markdown'
        )
        
        # Mark as active
        self.active_scans[user_id] = {'target': target, 'type': 'standard'}
        
        # Run in background thread
        thread = threading.Thread(
            target=self._run_scan_background,
            args=(update, target, modules, use_intelligence)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"User {user_id} started scan on {target}")
    
    def _run_scan_background(
        self,
        update: Update,
        target: str,
        modules: list,
        use_intelligence: bool
    ):
        """Run scan in background thread."""
        user_id = update.effective_user.id
        
        try:
            # Run scan
            engine = AthenaEngine(
                target_query=target,
                use_intelligence=use_intelligence,
                quiet=True
            )
            
            engine.run_scan(modules)
            
            # Generate report
            json_report = engine.generate_report('json')
            
            # Get summary
            summary = engine.profile.get_summary()
            
            # Send results
            message = f"""
✅ **Scan Complete!**

🎯 Target: `{target}`

📊 **Results:**
• Emails: {summary['emails']}
• Usernames: {summary['usernames']}
• Phone Numbers: {summary['phone_numbers']}
• Domains: {summary['domains']}
• Breaches: {summary['breaches']}
• IPs: {summary['related_ips']}

📄 Report saved: `{json_report.name}`

⏱️ Scan duration: {engine.profile.scan_duration:.2f}s
            """
            
            # Send message using asyncio
            import asyncio
            asyncio.run(update.message.reply_text(message, parse_mode='Markdown'))
            
            # Send detailed results if small enough
            if summary['emails'] > 0 and summary['emails'] <= 10:
                emails_text = "\n".join([f"• {email}" for email in engine.profile.emails])
                asyncio.run(update.message.reply_text(
                    f"📧 **Email Addresses:**\n{emails_text}",
                    parse_mode='Markdown'
                ))
            
            if summary['breaches'] > 0 and summary['breaches'] <= 5:
                breaches_text = "\n".join([
                    f"• {b.get('name', 'Unknown')} ({b.get('date', 'Unknown')})"
                    for b in engine.profile.breaches
                ])
                asyncio.run(update.message.reply_text(
                    f"⚠️ **Data Breaches:**\n{breaches_text}",
                    parse_mode='Markdown'
                ))
            
            logger.info(f"Scan completed for user {user_id}")
        
        except Exception as e:
            logger.error(f"Scan failed for user {user_id}: {e}")
            import asyncio
            asyncio.run(update.message.reply_text(
                f"❌ Scan failed: {str(e)}",
                parse_mode='Markdown'
            ))
        
        finally:
            # Remove from active scans
            if user_id in self.active_scans:
                del self.active_scans[user_id]
    
    def _run_deep_scan_background(self, update: Update, target: str, depth: int):
        """Run deep scan in background thread."""
        user_id = update.effective_user.id
        
        try:
            automator = Automator(max_depth=depth, quiet=True)
            results = automator.run_automated_chain(target)
            
            # Send results
            message = f"""
✅ **Deep Scan Complete!**

🎯 Initial Target: `{target}`
📊 Total Targets Scanned: {len(automator.scanned_targets)}
🌲 Scan Depth: {depth}

🔍 **Discovered Targets:**
{chr(10).join([f"• {t}" for t in list(automator.scanned_targets)[:10]])}
{f"... and {len(automator.scanned_targets) - 10} more" if len(automator.scanned_targets) > 10 else ""}
            """
            
            import asyncio
            asyncio.run(update.message.reply_text(message, parse_mode='Markdown'))
            
            logger.info(f"Deep scan completed for user {user_id}")
        
        except Exception as e:
            logger.error(f"Deep scan failed for user {user_id}: {e}")
            import asyncio
            asyncio.run(update.message.reply_text(
                f"❌ Deep scan failed: {str(e)}",
                parse_mode='Markdown'
            ))
        
        finally:
            if user_id in self.active_scans:
                del self.active_scans[user_id]
    
    def run(self):
        """Start the bot."""
        # Create application
        self.app = Application.builder().token(self.token).build()
        
        # Add command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("modules", self.modules_command))
        self.app.add_handler(CommandHandler("scan", self.scan_command))
        self.app.add_handler(CommandHandler("quickscan", self.quickscan_command))
        self.app.add_handler(CommandHandler("fullscan", self.fullscan_command))
        self.app.add_handler(CommandHandler("deepscan", self.deepscan_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        
        logger.info("Starting Telegram bot...")
        print("Bot started! Press Ctrl+C to stop.")
        
        # Start polling
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
