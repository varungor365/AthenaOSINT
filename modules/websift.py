"""
WebSift Module.
Rapidly extracts emails, phone numbers, and social links from websites.
Re-implementation of the core WebSift logic for AthenaOSINT.
"""
import requests
import re
from bs4 import BeautifulSoup
from loguru import logger
from core.engine import Profile

# Metadata
META = {
    'name': 'websift',
    'description': 'Extract Contacts (Email/Phone/Socials) from Websites',
    'category': 'scraper',
    'risk': 'safe', # passive scraping
    'emoji': '🕸️'
}

# Regex Patterns (Simplified)
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
PHONE_REGEX = r'\+?1?\d{9,15}' # Basic intl phone
SOCIAL_DOMAINS = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 'youtube.com', 'github.com', 't.me']

def scan(target: str, profile: Profile):
    """
    Scrapes the target URL for contact info.
    """
    if not target.startswith('http'):
        target = 'https://' + target

    logger.info(f"[WebSift] Sifting through {target}...")

    try:
        res = requests.get(target, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        
        if res.status_code != 200:
            logger.warning(f"[WebSift] URL returned status {res.status_code}")
            return

        text = res.text
        soup = BeautifulSoup(text, 'html.parser')

        # 1. Emails
        emails = set(re.findall(EMAIL_REGEX, text))
        for email in emails:
            # Filter junk
            if not any(x in email for x in ['.png', '.jpg', '.gif', '.css', '.js']):
                logger.info(f"  └─ Found Email: {email}")
                profile.add_email(email)

        # 2. Phones
        # Phone regex is tricky on raw text, better to look for tel: links or specific patterns
        # We'll rely on global regex for now but be careful of false positives
        # phones = set(re.findall(PHONE_REGEX, text))
        # for phone in phones:
        #    profile.add_phone(phone)
        
        # Better: Look for href="tel:..."
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('tel:'):
                phone = href.replace('tel:', '').strip()
                logger.info(f"  └─ Found Phone: {phone}")
                profile.add_phone(phone)
            
            # 3. Socials
            for domain in SOCIAL_DOMAINS:
                if domain in href:
                    logger.info(f"  └─ Found Social: {href}")
                    profile.add_metadata({'social_link': href})

        logger.success(f"[WebSift] Finished. Found {len(emails)} emails.")

    except Exception as e:
        logger.error(f"[WebSift] Failed: {e}")
        profile.add_error('websift', str(e))
